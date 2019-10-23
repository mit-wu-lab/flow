"""Load I-210 model and run the simulation."""

from flow.core.experiment import Experiment
from flow.core.params import AimsunParams, EnvParams, NetParams
from flow.core.params import VehicleParams
from flow.envs import TestEnv
from flow.networks import Network
from flow.core.params import InFlows
import flow.config as config
import os

sim_params = AimsunParams(
    sim_step=0.5,
    render=True,
    emission_path='data',
    subnetwork_name='Subnetwork 8037060',
    replication_name="Micro Profiled PM 16-21",
    centroid_config_name="Centroid Configuration 8037063")

env_params = EnvParams()
vehicles = VehicleParams()

template_path = os.path.join(config.PROJECT_PATH,
                             "flow/utils/aimsun/i_210_sub_merge.ang")
# template_path = '/Users/yashar/Dropbox/Berkeley/Projects/I-210/I-210Pasadena/i_210_sub_merge.ang'

network = Network(
    name="aimsun_small_template",
    vehicles=vehicles,
    net_params=NetParams(
        inflows=InFlows(),
        template=template_path
    )
)

env = TestEnv(env_params, sim_params, network, simulator='aimsun')
exp = Experiment(env)
exp.run(1, 50000)

