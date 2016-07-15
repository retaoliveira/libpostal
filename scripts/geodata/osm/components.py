import os
import six
import yaml

from geodata.address_formatting.formatter import AddressFormatter

this_dir = os.path.realpath(os.path.dirname(__file__))

OSM_BOUNDARIES_DIR = os.path.join(this_dir, os.pardir, os.pardir, os.pardir,
                                  'resources', 'boundaries', 'osm')


class OSMAddressComponents(object):
    '''
    Keeps a map of OSM keys and values to the standard components
    of an address like city, state, etc. used for address formatting.
    When we reverse geocode a point, it will fall into a number of
    polygons, and we simply need to assign the names of said polygons
    to an address field.
    '''

    ADMIN_LEVEL = 'admin_level'

    # These keys override country-level 
    global_keys = {
        'place': {
            'country': AddressFormatter.COUNTRY,
            'state': AddressFormatter.STATE,
            'region': AddressFormatter.STATE,
            'province': AddressFormatter.STATE,
            'county': AddressFormatter.STATE_DISTRICT,
            'island': AddressFormatter.ISLAND,
            'islet': AddressFormatter.ISLAND,
            'municipality': AddressFormatter.CITY,
            'city': AddressFormatter.CITY,
            'town': AddressFormatter.CITY,
            'township': AddressFormatter.CITY,
            'village': AddressFormatter.CITY,
            'hamlet': AddressFormatter.CITY,
            'borough': AddressFormatter.CITY_DISTRICT,
            'suburb': AddressFormatter.SUBURB,
            'quarter': AddressFormatter.SUBURB,
            'neighbourhood': AddressFormatter.SUBURB
        }
    }

    def __init__(self, boundaries_dir=OSM_BOUNDARIES_DIR):
        self.config = {}

        for filename in os.listdir(boundaries_dir):
            if not filename.endswith('.yaml'):
                continue

            country_code = filename.rsplit('.yaml', 1)[0]
            data = yaml.load(open(os.path.join(boundaries_dir, filename)))
            for prop, values in six.iteritems(data):
                for k, v in values.iteritems():
                    if isinstance(v, six.string_types) and v not in AddressFormatter.address_formatter_fields:
                        raise ValueError(u'Invalid value in {} for prop={}, key={}: {}'.format(filename, prop, k, v))
            self.config[country_code] = data

    def component(self, country, prop, value):
        props = self.global_keys.get(prop, {})
        if not props:
            props = self.config.get(country, {}).get(prop, {})
        return props.get(value, None)

    def component_from_properties(self, country, properties, containing=()):
        country_config = self.config.get(country, {})

        config = country_config

        overrides = country_config.get('overrides')
        if overrides:
            id_overrides = overrides.get('id', {})
            element_type = properties.get('type')
            element_id = properties.get('id')

            override_value = id_overrides.get(element_type, {}).get(six.binary_type(element_id or ''), None)
            if override_value:
                return override_value

            contained_by_overrides = overrides.get('contained_by')
            if contained_by_overrides and containing:
                # Note, containing should be passed in from smallest to largest
                for containing_type, containing_id in containing:
                    config_updates = contained_by_overrides.get(containing_type, {}).get(six.binary_type(containing_id or ''), None)
                    print contained_by_overrides
                    if config_updates:
                        config.update(config_updates)
                        break

        for k, v in six.iteritems(properties):
            containing_component = self.global_keys.get(k, {}).get(v, None)

            if containing_component is not None:
                return containing_component

        for k, v in six.iteritems(properties):
            if containing_component is None:
                containing_component = config.get(k, {}).get(v, None)

            if containing_component is not None:
                return containing_component

        return None

osm_address_components = OSMAddressComponents()
