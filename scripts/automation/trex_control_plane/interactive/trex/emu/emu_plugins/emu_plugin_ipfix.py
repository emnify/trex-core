from trex.emu.api import *
from trex.emu.emu_plugins.emu_plugin_base import *
from trex.emu.trex_emu_validator import EMUValidator
import trex.utils.parsing_opts as parsing_opts


class IPFIXPlugin(EMUPluginBase):
    """
        Defines a Netflow/IPFIX plugin according of `Netflow v9 - RFC 3954 <https://tools.ietf.org/html/rfc3954>`_  or 
        `Netflow v10 (IPFix) - RFC 7011 <https://tools.ietf.org/html/rfc7011>`_ 
    """

    plugin_name = 'IPFIX'

    # init json examples for SDK
    INIT_JSON_NS = None
    """
    There is currently no NS init json for IPFix.
    """

    INIT_JSON_CLIENT = { 'ipfix': "Pointer to INIT_JSON_CLIENT below" }
    """
    `IPFix INIT_JSON_CLIENT:  <https://trex-tgn.cisco.com/trex/doc/trex_emu.html#_netflow_plugin>`_ 

    :parameters:

        netflow_version: uint16
            Netflow version. Might be 9 or 10, notice version 9 doesn't support variable length fields or per enterprise fields. Defaults to 10.

        dst_mac: [6]bytes
            Optional, destination MAC address. If not supplied, the destination MAC address will be the default gateway's MAC address,
            in case there is one.

        dst_ipv4: [4]byte
            The collector's IPv4 address. Optional, in case you provide dst_ipv6. One of {dst_ipv4, dst_ipv6} must be provided but not both.

        dst_ipv6: [16]byte
            The collector's IPv6 address. Optional, in case you provide dst_ipv4. One of {dst_ipv4, dst_ipv6} must be provided but not both.

        dst_port: uint16
            Collector's L4 port, defaults to 4739.

        src_port: uint16
            Exporter's L4 port, defaults to 30334.

        domain_id: uint32
            The observation domain ID as defined in IPFix. If not provided, it will be randomly generated.

        generators: list
            List of generators, where each generator is a dictionary.

    :generators:

        name: string
            Name of the generator. This field is required.

        auto_start: bool
            If true will automatically start sending IPFix packets upon creation.

        rate_pps: float32
            Rate of IPFix data packets (in pps), defaults to 3.

        data_records_num: uint32
            Number of data records in each data packet. If not provided, it will default to the maximum number of data packets which doesn't
            exceed the MTU.

        template_id: uint16
            The template ID for this generator. Must be greater than 255. This field is required. Each generator must have a unique template identifier.

        is_options_template: bool
            Indicates if this is generator will send Options Template (True) packets or Data Template packets (False). Defaults to False.

        scope_count: uint16
            Scope count in case of Options Template packets. Must be bigger than 0.

        fields: list
            List of fields for this generator. Fields are very much alike the fields of Netflow. Each field is represented by a dictionary.

        engines: list
            List of engines for this generator. Each engine is represented by a dictionary.

    :fields:

        name: string
            Name of this field. The name is required.

        type: uint16
            A uint16 that is unique per type. One can consult the RFC for specific values of types.

        length: uint16
            Length of this field in bytes. If the value is 0xFFFF, this indicates variable length fields. Variable length fields are not supported
            at the moment. Variable lengths are supported only in V10.

        enterprise_number: uint32
            Enterprise number in case the field is specific per enterprise and the type's MSB equals 1 to indicate this is an enterprise field.
            Enterprise fields are supported only in V10.

        data: [`length`]bytes
            List of bytes of size length. This will be the initial data in data packets and can be modified by the engines.

    :engines:
    
        engine_name: string
            Name of the engine. Must be the name of one of the fields.

        engine_type: string
            Type of engine, can be {uint, histogram_uint, histogram_uint_range, histogram_uint_list, histogram_uint64, histogram_uint64_range, histogram_uint64_list}

        params: dictionary
            Dictionary of params for the engine. Each engine type has different params. Explore the EMU documentation `engine section <https://trex-tgn.cisco.com/trex/doc/trex_emu.html#_engines>`_
            for more information on engines.
    """


    def __init__(self, emu_client):
        """
        Initialize an IPFixPlugin.

            :parameters:
                emu_client: :class:`trex.emu.trex_emu_client.EMUClient`
                    Valid EMU client.
        """
        super(IPFIXPlugin, self).__init__(emu_client, 'ipfix_c_cnt')

    # API methods
    @client_api('getter', True)
    def get_gen_info(self, c_key):
        """
            Gets information about all the generators of a client.

            :parameters:

                c_key: :class:`trex.emu.trex_emu_profile.EMUClientKey`
                    EMUClientKey

            :returns: list of dictionaries

                    For each generator we get a key value mapping of name with the following parameters:

                    { 'enabled': bool
                        Flag indicating if generator is enabled.

                    'options_template': bool
                        Flag indicating if we are sending options templates for this generator or data templates.

                    'scope_count': uint16
                        Scope count in case of options template, otherwise will be 0.

                    'template_rate_pps': float32
                        The rate of template packets in pps.

                    'data_rate_pps': float32
                        The rate of data packets in pps.

                    'data_records_num': float32
                        The number of data records in a packet as user specified.

                    'data_records_num_send': float32
                        The actual number of data records in a packet as TRex calculated. For example, if user provided 0,
                        then TRex calculates the maximum number based on the MTU.

                    'fields_num': int
                        Number of fields in this generator.

                    'engines_num': int
                        Number of engines in this generator.}
        """
        ver_args = [{'name': 'c_key', 'arg': c_key, 't': EMUClientKey}]
        EMUValidator.verify(ver_args)
        res = self.emu_c._send_plugin_cmd_to_client('ipfix_c_get_gens_info', c_key)
        return res.get('generators_info', {})

    @client_api('command', True)
    def set_gen_rate(self, c_key, gen_name, rate):
        """
            Set a new rate of data packets for an IPFix generator.

            :parameters:

                c_key: :class:`trex.emu.trex_emu_profile.EMUClientKey`
                    EMUClientKey

                gen_name: string
                    The name of the generator we are trying to alter.

                rate: float32
                    New rate for data packets, in pps.

            :returns:
               bool : Flag indicating the result of the operation.
        """
        ver_args = [{'name': 'c_key', 'arg': c_key, 't': EMUClientKey},
                    {'name': 'gen_name', 'arg': gen_name, 't': str},
                    {'name': 'rate', 'arg': rate, 't': float}]
        EMUValidator.verify(ver_args)
        return self.emu_c._send_plugin_cmd_to_client('ipfix_c_set_gen_state', c_key=c_key, gen_name=gen_name, rate=rate)

    @client_api('command', True)
    def enable_generator(self, c_key, gen_name, enable):
        """
            Enable/disable an IPFix generator.

            :parameters:

                c_key: :class:`trex.emu.trex_emu_profile.EMUClientKey`
                    EMUClientKey

                gen_name: string
                    The name of the generator to alter.

                enable: bool
                    True if we wish to enable the generator, False if we wish to disable it.

            :returns:
               bool : Flag indicating the result of the operation.
        """
        ver_args = [{'name': 'c_key', 'arg': c_key, 't': EMUClientKey},
                    {'name': 'gen_name', 'arg': gen_name, 't': str},
                    {'name': 'enable', 'arg': enable, 't': bool}]
        EMUValidator.verify(ver_args)
        return self.emu_c._send_plugin_cmd_to_client('ipfix_c_set_gen_state', c_key=c_key, gen_name=gen_name, enable=enable)

    # Plugins methods
    @plugin_api('ipfix_show_counters', 'emu')
    def ipfix_show_counters_line(self, line):
        """Show IPFix data counters data.\n"""
        parser = parsing_opts.gen_parser(self,
                                        "show_counters_ipfix",
                                        self.ipfix_show_counters_line.__doc__,
                                        parsing_opts.EMU_SHOW_CNT_GROUP,
                                        parsing_opts.EMU_NS_GROUP,
                                        parsing_opts.MAC_ADDRESS,
                                        parsing_opts.EMU_DUMPS_OPT
                                        )

        opts = parser.parse_args(line.split())
        self.emu_c._base_show_counters(self.data_c, opts, req_ns = True)
        return True

    @plugin_api('ipfix_get_gen_info', 'emu')
    def ipfix_get_gen_info_line(self, line):
        """Get IPFix generators information.\n"""
        parser = parsing_opts.gen_parser(self,
                                        "ipfix_get_gens_info",
                                        self.ipfix_get_gen_info_line.__doc__,
                                        parsing_opts.EMU_NS_GROUP_NOT_REQ,
                                        parsing_opts.MAC_ADDRESS,
                                        parsing_opts.EMU_DUMPS_OPT,
                                        )

        opts = parser.parse_args(line.split())
        self._validate_port(opts)
        ns_key = EMUNamespaceKey(opts.port, opts.vlan, opts.tpid)
        c_key = EMUClientKey(ns_key, opts.mac)
        res = self.get_gen_info(c_key)

        if opts.json or opts.yaml:
            dump_json_yaml(data = res, to_json = opts.json, to_yaml = opts.yaml)
            return
    
        keys_to_headers = [ {'key': 'name',                     'header': 'Name'},
                            {'key': 'template_id',              'header': 'Temp. ID'},
                            {'key': 'enabled',                  'header': 'Enabled'},
                            {'key': 'options_template',         'header': 'Opt. Temp.'},
                            {'key': 'scope_count',              'header': 'Scope cnt'},
                            {'key': 'template_rate_pps',        'header': 'Temp. Rate'},
                            {'key': 'data_rate_pps',            'header': 'Data Rate'},
                            {'key': 'data_records_num',         'header': '# Records spec.'},
                            {'key': 'data_records_num_send',    'header': '# Records calc.'},
                            {'key': 'fields_num',               'header': '# Fields'},
                            {'key': 'engines_num',              'header': '# Engines'},
        ]

        for gen_name, gen_info in res.items():
            gen_info['name'] = gen_name
        self.print_table_by_keys(res.values(), keys_to_headers, title="Generators")

    @plugin_api('ipfix_enable_gen', 'emu')
    def ipfix_enable_gen_line(self, line):
        """Enable an IPFIx generator.\n"""
        res = self._enable_disable_gen_line(line, self.ipfix_enable_gen_line, "enable")
        self.logger.post_cmd(res)

    @plugin_api('ipfix_disable_gen', 'emu')
    def ipfix_disable_gen_line(self, line):
        """Disable an IPFIx generator.\n"""
        res = self._enable_disable_gen_line(line, self.ipfix_enable_gen_line, "disable")
        self.logger.post_cmd(res)

    def _enable_disable_gen_line(self, line, caller_func, enable_disable):
        parser = parsing_opts.gen_parser(self,
                                        "ipfix_enable_gen",
                                        caller_func.__doc__,
                                        parsing_opts.EMU_NS_GROUP_NOT_REQ,
                                        parsing_opts.MAC_ADDRESS,
                                        parsing_opts.GEN_NAME,
                                        )

        opts = parser.parse_args(line.split())
        self._validate_port(opts)
        ns_key = EMUNamespaceKey(opts.port, opts.vlan, opts.tpid)
        c_key = EMUClientKey(ns_key, opts.mac)
        return self.enable_generator(c_key, opts.gen_name, enable_disable == 'enable')

    @plugin_api('ipfix_set_data_rate', 'emu')
    def ipfix_set_data_rate_line(self, line):
        """Set IPFix generator data rate.\n"""
        parser = parsing_opts.gen_parser(self,
                                        "ipfix_set_data_rate",
                                        self.ipfix_set_data_rate_line.__doc__,
                                        parsing_opts.EMU_NS_GROUP_NOT_REQ,
                                        parsing_opts.MAC_ADDRESS,
                                        parsing_opts.GEN_NAME,
                                        parsing_opts.GEN_RATE,
                                        )

        opts = parser.parse_args(line.split())
        self._validate_port(opts)
        ns_key = EMUNamespaceKey(opts.port, opts.vlan, opts.tpid)
        c_key = EMUClientKey(ns_key, opts.mac)
        return self.set_gen_rate(c_key, opts.gen_name, opts.rate)
