"""Contains an experiment class for running simulations."""

import logging
import datetime
import numpy as np
import time
import os

from flow.core.util import emission_to_csv


class Experiment:
    """
    Class for systematically running simulations in any supported simulator.

    This class acts as a runner for a network and environment. In order to use
    it to run an network and environment in the absence of a method specifying
    the actions of RL agents in the network, type the following:

        >>> from flow.envs import Env
        >>> env = Env(...)
        >>> exp = Experiment(env)  # for some env
        >>> exp.run(num_runs=1, num_steps=1000)

    If you wish to specify the actions of RL agents in the network, this may be
    done as follows:

        >>> rl_actions = lambda state: 0  # replace with something appropriate
        >>> exp.run(num_runs=1, num_steps=1000, rl_actions=rl_actions)

    Finally, if you would like to plot and visualize your results, this
    class can generate csv files from emission files produced by SUMO. These
    files will contain the speeds, positions, edges, etc. of every vehicle
    in the network at every time step.

    In order to ensure that the simulator constructs an emission file, set the
    ``emission_path`` attribute in ``SimParams`` to some path.

        >>> from flow.core.params import SimParams
        >>> sim_params = SimParams(emission_path="./data")

    Once you have included this in your environment, run your Experiment object
    as follows:

        >>> exp.run(num_runs=1, num_steps=1000, convert_to_csv=True)

    After the experiment is complete, look at the "./data" directory. There
    will be two files, one with the suffix .xml and another with the suffix
    .csv. The latter should be easily interpretable from any csv reader (e.g.,
    Excel), and can be parsed using tools such as numpy and pandas.

    Attributes
    ----------
    env : flow.envs.Env
        the environment object the simulator will run
    """

    def __init__(self, env):
        """Instantiate Experiment."""
        self.env = env

        logging.info("Starting experiment {} at {}".format(
            env.network.name, str(datetime.datetime.utcnow())))

        logging.info("Initializing environment.")

    def run(self, num_runs, num_steps, rl_actions=None, convert_to_csv=False, output_to_terminal=True):
        """Run the given network for a set number of runs and steps per run.

        Parameters
        ----------
        num_runs : int
            number of runs the experiment should perform
        num_steps : int
            number of steps to be performed in each run of the experiment
        rl_actions : method, optional
            maps states to actions to be performed by the RL agents (if
            there are any)
        convert_to_csv : bool
            Specifies whether to convert the emission file created by sumo
            into a csv file

        Returns
        -------
        info_dict : dict
            contains returns, average speed per step
        """
        # raise an error if convert_to_csv is set to True but no emission
        # file will be generated, to avoid getting an error at the end of the
        # simulation
        if convert_to_csv and self.env.sim_params.emission_path is None:
            raise ValueError(
                'The experiment was run with convert_to_csv set '
                'to True, but no emission file will be generated. If you wish '
                'to generate an emission file, you should set the parameter '
                'emission_path in the simulation parameters (SumoParams or '
                'AimsunParams) to the path of the folder where emissions '
                'output should be generated. If you do not wish to generate '
                'emissions, set the convert_to_csv parameter to False.')

        info_dict = {}
        if rl_actions is None:
            def rl_actions(*_):
                return None

        rets = [] # returns
        mean_rets = []
        ret_lists = []
        vels = []
        mean_vels = []
        std_vels = []
        outflows = []
        inflows = []

        # for each run
        for i in range(num_runs):
            vel = np.zeros(num_steps)
            logging.info("Iter #" + str(i))
            ret = 0
            ret_list = []
            state = self.env.reset()

            # for each step
            for j in range(num_steps):

                # get the states, rewards, etc.
                state, reward, done, _ = self.env.step(rl_actions(state))

                # get speeds at all simulation steps
                vel[j] = np.mean(self.env.k.vehicle.get_speed(self.env.k.vehicle.get_ids()))

                # compute the return as cumulative reward for all simulation steps
                ret += reward
                ret_list.append(reward)

                if done:
                    break

            rets.append(ret)
            vels.append(vel)
            mean_rets.append(np.mean(ret_list))
            ret_lists.append(ret_list)
            mean_vels.append(np.mean(vel))
            std_vels.append(np.std(vel))

            # get the outflows and inflows for the past 500 seconds, if the simulation is less than
            # 500 seconds then the following will get all inflows (the number of vehicles entering the network)
            # and outflows (the number of vehicles leaving the network) during the entire simulation time span
            outflows.append(self.env.k.vehicle.get_outflow_rate(int(500)))

            ######################
            ### added by Weizi ###
            inflows.append(self.env.k.vehicle.get_inflow_rate(int(500)))
            if np.all(np.array(inflows) > 1e-5):
                throughput = [x / y for x, y in zip(outflows, inflows)]
            else:
                throughput = [0] * len(inflows)
            ######################

        info_dict["returns"] = rets
        info_dict["velocities"] = vels
        info_dict["mean_returns"] = mean_rets
        info_dict["per_step_returns"] = ret_lists
        info_dict["mean_outflows"] = np.mean(outflows)

        if output_to_terminal:
            print("Round {0} -- Return: {1}".format(i, ret))
            print("Return: {} (avg), {} (std)".format(
                np.around(np.mean(rets), decimals=2), np.around(np.std(rets), decimals=2)))

            print("Speed (m/s): {} (avg), {} (std)".format(
                np.around(np.mean(mean_vels), decimals=2), np.around(np.std(mean_vels), decimals=2)))

            ### added by Weizi ###
            print("Throughput (veh/hr): {} (avg), {} (std)".format(np.around(np.mean(throughput), decimals=2),
                                                np.around(np.std(throughput), decimals=2)))

        ### added by Weizi ###
        info_dict["avg_spd"] = np.around(np.mean(mean_vels), decimals=2)
        info_dict["avg_tpt"] = np.around(np.mean(throughput), decimals=2)


        self.env.terminate()

        if convert_to_csv:
            # wait a short period of time to ensure the xml file is readable
            time.sleep(0.1)

            # collect the location of the emission file
            dir_path = self.env.sim_params.emission_path
            emission_filename = "{0}-emission.xml".format(self.env.network.name)
            emission_path = os.path.join(dir_path, emission_filename)

            # convert the emission file into a csv
            emission_to_csv(emission_path)

            # Delete the .xml version of the emission file.
            os.remove(emission_path)

        return info_dict
