from sparkx.flow import FlowInterface
import numpy as np

class ReactionPlaneFlow(FlowInterface.FlowInterface):
    
    """
    This class implements a reaction plane flow analysis algorithm 
    
    For this method, the flow is calculated under the assumption that the event plane angle is constant 
    throughout all events. The flow is calculated as

    .. math::

        v_n = \\langle p_T^n \\exp{\\frac{in\\phi_i}{p_T^n}}\\rangle
    
    where we average over all particles of all events. We return complex numbers, which contain the information
    about the position of the event plane.
    
    
    Parameters
    ----------
    n : int, optional
        The value of the harmonic. Default is 2.
   
    Example
    --------
    
    A demonstration how to calculate flow according to the event plane of a separate particle list.
    The same particle list can also be used to determine the event plane and the flow.

    .. highlight:: python
    .. code-block:: python
        :linenos:

        >>> from Jetscape import Jetscape
        >>> from flow.EventPlaneFlow import EventPlaneFlow
        >>>
        >>> JETSCAPE_FILE_PATH_FLOW = [Jetscape_directory]/particle_lists_flow.dat
       
        >>> # Jetscape object containing the particles on which we want to calculate flow
        >>> jetscape_flow = Jetscape(JETSCAPE_FILE_PATH_FLOW)
        >>>
        >>> # Create flow objects for v2
        >>> flow2 = ReactionPlaneFlow(n=2)
        >>>
        >>> # Calculate the integrated flow with error
        >>> v2, v2_error = flow2.integrated_flow(jetscape_flow)
 
       

    """
    def __init__(self,n=2):
        """
        Initialize the ReactionPlaneFlow object.

        Parameters
        ----------
        n : int, optional
            The value of the harmonic. Default is 2.
        """
        if not isinstance(n, int):
            raise TypeError('n has to be int')
        elif n <= 0:
            raise ValueError('n-th harmonic with value n<=0 can not be computed')
        else:
            self.n_ = n

    def integrated_flow(self, particle_data):
        """
        Compute the integrated flow.

        Parameters
        ----------
        particle_data : list
            List of particle data.

        Returns
        -------
        complex
            The integrated flow value, represented as a complex number.
        """
        flow_event_average = 0. + 0.j
        number_particles = 0.
        for event in range(len(particle_data)):
            flow_event = 0. + 0.j
            for particle in range(len(particle_data[event])):
                weight = 1. if particle_data[event][particle].weight is None else particle_data[event][particle].weight
                pt = particle_data[event][particle].pt_abs()
                phi = particle_data[event][particle].phi()
                flow_event += weight*(pt**self.n_ * np.exp(1j*self.n_*phi) / pt**self.n_)
                number_particles += weight
            if number_particles != 0.:
                flow_event_average += flow_event
            else:
                flow_event_average = 0. + 0.j
        flow_event_average /= number_particles
        return flow_event_average

    def differential_flow(self,particle_data,bins,flow_as_function_of):
        """
        Compute the differential flow.

        Parameters
        ----------
        particle_data : list
            List of particle data.
        bins : list or np.ndarray
            Bins used for the differential flow calculation.
        flow_as_function_of : str
            Variable on which the flow is calculated ("pt", "rapidity", or "pseudorapidity").

        Returns
        -------
        list
            A list of complex numbers representing the flow values for each bin.
        """
        if not isinstance(bins, (list,np.ndarray)):
            raise TypeError('bins has to be list or np.ndarray')
        if not isinstance(flow_as_function_of, str):
            raise TypeError('flow_as_function_of is not a string')
        if flow_as_function_of not in ["pt","rapidity","pseudorapidity"]:
            raise ValueError("flow_as_function_of must be either 'pt', 'rapidity', 'pseudorapidity'")

        particles_bin = []
        for bin in range(len(bins)-1):
            events_bin = []
            for event in range(len(particle_data)):
                particles_event = []
                for particle in particle_data[event]:
                    val = 0.
                    if flow_as_function_of == "pt":
                        val = particle.pt_abs()
                    elif flow_as_function_of == "rapidity":
                        val = particle.momentum_rapidity_Y()
                    elif flow_as_function_of == "pseudorapidity":
                        val = particle.pseudorapidity()
                        print(val)
                    if val >= bins[bin] and val < bins[bin+1]:
                        particles_event.append(particle)
                events_bin.extend([particles_event])
            particles_bin.extend([events_bin])

        return self.__differential_flow_calculation(particles_bin)

    def __differential_flow_calculation(self, binned_particle_data):
        flow_differential = [0.+0.j for i in range(len(binned_particle_data))]
        for bin in range(len(binned_particle_data)):
            number_particles = 0.
            flow_event_average = 0. + 0.j
            for event in range(len(binned_particle_data[bin])):
                flow_event = 0. + 0.j
                for particle in range(len(binned_particle_data[bin][event])):
                    weight = 1. if binned_particle_data[bin][event][particle].weight is None else binned_particle_data[bin][event][particle].weight
                    pt = binned_particle_data[bin][event][particle].pt_abs()
                    phi = binned_particle_data[bin][event][particle].phi()
                    flow_event += weight*(pt**self.n_ * np.exp(1j*self.n_*phi) / pt**self.n_)
                    number_particles += weight
                flow_event_average += flow_event
            if number_particles != 0.:
                flow_event_average /= number_particles
            else:
                flow_event_average = 0. + 0.j
            flow_differential[bin] = flow_event_average
        return flow_differential
