"""Contains the figure eight scenario class."""

import numpy as np
from numpy import pi, sin, cos, linspace

from flow.core.params import InitialConfig
from flow.core.params import TrafficLightParams
from flow.scenarios.base_scenario import Scenario

ADDITIONAL_NET_PARAMS = {
    # radius of the circular components
    "radius_ring": 30,
    # number of lanes
    "lanes": 1,
    # speed limit for all edges
    "speed_limit": 30,
    # resolution of the curved portions
    "resolution": 40
}


class Figure8Scenario(Scenario):
    """Figure eight scenario class."""

    def __init__(self,
                 name,
                 vehicles,
                 net_params,
                 initial_config=InitialConfig(),
                 traffic_lights=TrafficLightParams()):
        """Initialize a figure 8 scenario.

        Requires from net_params:
        - ring_radius: radius of the circular portions of the network. Also
          corresponds to half the length of the perpendicular straight lanes.
        - resolution: number of nodes resolution in the circular portions
        - lanes: number of lanes in the network
        - speed: max speed of vehicles in the network

        In order for right-of-way dynamics to take place at the intersection,
        set "no_internal_links" in net_params to False.

        See flow/scenarios/base_scenario.py for description of params.
        """
        for p in ADDITIONAL_NET_PARAMS.keys():
            if p not in net_params.additional_params:
                raise KeyError('Network parameter "{}" not supplied'.format(p))

        ring_radius = net_params.additional_params["radius_ring"]
        self.ring_edgelen = ring_radius * np.pi / 2.
        self.intersection_len = 2 * ring_radius
        self.junction_len = 2.9 + 3.3 * net_params.additional_params["lanes"]
        self.inner_space_len = 0.28

        # instantiate "length" in net params
        net_params.additional_params["length"] = \
            6 * self.ring_edgelen + 2 * self.intersection_len + \
            2 * self.junction_len + 10 * self.inner_space_len

        self.radius_ring = net_params.additional_params["radius_ring"]
        self.length = net_params.additional_params["length"]
        self.lanes = net_params.additional_params["lanes"]
        self.resolution = net_params.additional_params["resolution"]

        super().__init__(name, vehicles, net_params, initial_config,
                         traffic_lights)

    def specify_nodes(self, net_params):
        """See parent class."""
        r = net_params.additional_params["radius_ring"]

        nodes = [{
            "id": "center",
            "x": 0,
            "y": 0,
            "radius": (2.9 + 3.3 * net_params.additional_params["lanes"])/2,
            "type": "priority"
        }, {
            "id": "right",
            "x": r,
            "y": 0,
            "type": "priority"
        }, {
            "id": "top",
            "x": 0,
            "y": r,
            "type": "priority"
        }, {
            "id": "left",
            "x": -r,
            "y": 0,
            "type": "priority"
        }, {
            "id": "bottom",
            "x": 0,
            "y": -r,
            "type": "priority"
        }]

        return nodes

    def specify_edges(self, net_params):
        """See parent class."""
        r = net_params.additional_params["radius_ring"]
        resolution = net_params.additional_params["resolution"]
        ring_edgelen = 3 * r * pi / 2.
        intersection_edgelen = 2 * r

        # intersection edges
        edges = [{
            "id": "bottom",
            "type": "edgeType",
            "priority": "78",
            "from": "bottom",
            "to": "center",
            "length": intersection_edgelen / 2
        }, {
            "id": "top",
            "type": "edgeType",
            "priority": 78,
            "from": "center",
            "to": "top",
            "length": intersection_edgelen / 2
        }, {
            "id": "right",
            "type": "edgeType",
            "priority": 46,
            "from": "right",
            "to": "center",
            "length": intersection_edgelen / 2
        }, {
            "id": "left",
            "type": "edgeType",
            "priority": 46,
            "from": "center",
            "to": "left",
            "length": intersection_edgelen / 2
        }]

        # ring edges
        edges += [{
            "id": "upper_ring",
            "type": "edgeType",
            "from": "top",
            "to": "right",
            "length": ring_edgelen,
            "shape": [(r * (1 - cos(t)), r * (1 + sin(t)))
                      for t in linspace(0, 3 * pi / 2, resolution)]
        }, {
            "id": "lower_ring",
            "type": "edgeType",
            "from": "left",
            "to": "bottom",
            "length": ring_edgelen,
            "shape": [(-r + r * cos(t), -r + r * sin(t))
                      for t in linspace(pi / 2, 2 * pi, resolution)]
        }]

        return edges

    def specify_types(self, net_params):
        """See parent class."""
        lanes = net_params.additional_params["lanes"]
        speed_limit = net_params.additional_params["speed_limit"]
        types = [{
            "id": "edgeType",
            "numLanes": lanes,
            "speed": speed_limit
        }]

        return types

    def specify_routes(self, net_params):
        """See parent class."""
        rts = {
            "bottom":
                ["bottom", "top", "upper_ring", "right", "left", "lower_ring"],
            "top":
                ["top", "upper_ring", "right", "left", "lower_ring", "bottom"],
            "upper_ring":
                ["upper_ring", "right", "left", "lower_ring", "bottom", "top"],
            "left":
                ["left", "lower_ring", "bottom", "top", "upper_ring", "right"],
            "right":
                ["right", "left", "lower_ring", "bottom", "top", "upper_ring"],
            "lower_ring":
                ["lower_ring", "bottom", "top", "upper_ring", "right", "left"],
        }

        return rts

    def specify_connections(self, net_params):
        """See parent class."""
        lanes = net_params.additional_params["lanes"]
        conn_dict = {}
        conn = []
        for i in range(lanes):
            conn += [{"from": "bottom",
                      "to": "top",
                      "fromLane": str(i),
                      "toLane": str(i)}]
            conn += [{"from": "right",
                      "to": "left",
                      "fromLane": str(i),
                      "toLane": str(i)}]
        conn_dict["center"] = conn
        return conn_dict

    def specify_edge_starts(self):
        """See base class."""
        edgestarts = [
            ("bottom", 0),
            ("top", self.intersection_len / 2 + self.junction_len),
            ("upper_ring", self.intersection_len + self.junction_len),
            ("right", self.intersection_len + 3 * self.ring_edgelen
             + self.junction_len),
            ("left", 3 / 2 * self.intersection_len + 3 * self.ring_edgelen
             + 2 * self.junction_len),
            ("lower_ring", 2 * self.intersection_len + 3 * self.ring_edgelen
             + 2 * self.junction_len)]

        return edgestarts

    def specify_intersection_edge_starts(self):
        """See base class."""
        intersection_edgestarts = \
            [(":center_{}".format(self.lanes), self.intersection_len / 2),
             (":center_0", 3 / 2 * self.intersection_len
              + 3 * self.ring_edgelen + self.junction_len),
             # for aimsun
             ("bottom_to_top", self.intersection_len / 2),
             ("right_to_left", 3 / 2 * self.intersection_len
              + 3 * self.ring_edgelen + self.junction_len)]

        return intersection_edgestarts

    # def specify_internal_edge_starts(self):
    #     """See base class."""
    #     internal_edgestarts = \
    #         [(":bottom", 0),
    #          (":top", 0),
    #          (":right", 0),
    #          (":left", 0)]
    #
    #     return internal_edgestarts
