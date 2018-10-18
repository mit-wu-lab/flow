"""Contains the generator class for .net.xml files."""

from flow.core.generator import Generator
from flow.core.traffic_lights import TrafficLights

from lxml import etree
import xml.etree.ElementTree as ElementTree

E = etree.Element


class NetFileGenerator(Generator):
    """Class used to generate network files from a .net.xml file.

    The .net.xml file is specified in the NetParams object. For example:

        >>> from flow.core.params import NetParams
        >>> net_params = NetParams(netfile="/path/to/netfile.net.xml")

    No "specify_nodes" and "specify_edges" routes are needed. However, a
    "specify_routes" file is still needed to specify the appropriate routes
    vehicles can traverse in the network.
    """

    def generate_net(self, net_params, traffic_lights):
        """See parent class.

        The network file is generated from the .osm file specified in
        net_params.osm_path
        """
        # name of the .net.xml file (located in cfg_path)
        self.netfn = net_params.netfile

        # collect data from the generated network configuration file
        edges_dict, conn_dict = self._import_edges_from_net()

        return edges_dict, conn_dict

    def specify_nodes(self, net_params):
        """See class definition."""
        pass

    def specify_edges(self, net_params):
        """See class definition."""
        pass


    def _import_routes_from_net(self, filename):
        """Import route from a configuration file.

        This is a utility function for computing route information. It imports a
        network configuration file, and returns the information on the routes
        taken by all the vehicle located in the file.

        Parameters
        ----------
        filename : str type
            path to the xml file to load

        Returns
        -------
        routes_data : dict <dict>
            Key = name of the first route taken
            Element = list of all the routes taken by the vehicle starting in that route

        """
        # import the .net.xml file containing all edge/type data
        parser = etree.XMLParser(recover=True)
        tree = ElementTree.parse(filename, parser=parser)

        root = tree.getroot()

        # Collect information on the available types (if any are available).
        # This may be used when specifying some route data.
        routes_data = dict()


        for vehicle in root.findall('vehicle'):
            for route in vehicle.findall('route'):
                route_edges = route.attrib["edges"].split(' ')
                key=route_edges[0]
                if key in routes_data.keys():
                    for routes in routes_data[key]:
                        if routes==route_edges:
                            pass
                        else:
                            routes_data[key].append(route_edges)
                else:
                    routes_data[key] = [route_edges]
        return routes_data


        def specify_routes(self, filename):
            """ Format all the routes from the xml file

            Parameters
            ----------
            filename : str type
                path to the rou.xml file to load

            Returns
            -------
            routes_data : dict <dict>
                Key = name of the first route taken
                Element = list of all the routes taken by the vehicle starting in that route

            """
            return _import_routes_from_net(filename)

        def _import_tls_from_net(self,filename):
            """Import traffic lights from a configuration file.
             This is a utility function for computing traffic light information. It imports a
            network configuration file, and returns the information of the traffic lights in the file.

            Parameters
            ----------
            filename : str type
                path to the rou.xml file to load

             Returns
            -------
            tl_logic : TrafficLights
             """

            # import the .net.xml file containing all edge/type data
            parser = etree.XMLParser(recover=True)
            tree = ElementTree.parse(filename, parser=parser)
            root = tree.getroot()

            # create TrafficLights() class object to store traffic lights information from the file
            tl_logic = TrafficLights()
            for tl in root.findall('tlLogic'):
                phases = [phase.attrib for phase in tl.findall('phase')]
                tl_logic.add(tl.attrib['id'], tl.attrib['type'], tl.attrib['programID'], tl.attrib['offset'], phases)

            return tl_logic
