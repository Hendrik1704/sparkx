#===================================================
#
#    Copyright (c) 2024
#      SPARKX Team
#
#    GNU General Public License (GPLv3 or later)
#
#===================================================

from sparkx.Loader.BaseLoader import BaseLoader
from sparkx.Filter import *
import os

class JetscapeLoader(BaseLoader):
        
    def __init__(self, JETSCAPE_FILE):

        """
        Parameters
        ----------
        OSCAR_FILE : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Raises
        ------
        TypeError
            DESCRIPTION.

        Returns
        -------
        None
        """
        super().__init__(JETSCAPE_FILE)
        if not '.dat' in JETSCAPE_FILE:
            raise FileNotFoundError('File not found or does not end with .dat')

        self.PATH_JETSCAPE_ = JETSCAPE_FILE
        self.particle_type_ = 'hadron'

    def load(self, **kwargs):
        self.optional_arguments_ = kwargs
        self.event_end_lines_ = []

        for keys in self.optional_arguments_.keys():
            if keys not in ['events', 'filters', 'particletype']:
                raise ValueError('Unknown keyword argument used in constructor')

        if 'events' in self.optional_arguments_.keys() and isinstance(self.optional_arguments_['events'], tuple):
            self._check_that_tuple_contains_integers_only(self.optional_arguments_['events'])
            if self.optional_arguments_['events'][0] > self.optional_arguments_['events'][1]:
                raise ValueError('First value of event number tuple must be smaller than second value')
            elif self.optional_arguments_['events'][0] < 0 or self.optional_arguments_['events'][1] < 0:
                raise ValueError('Event numbers must be positive')
        elif 'events' in self.optional_arguments_.keys() and isinstance(self.optional_arguments_['events'], int):
            if self.optional_arguments_['events'] < 0:
                raise ValueError('Event number must be positive')
        
        if 'particletype' in self.optional_arguments_.keys() and isinstance(self.optional_arguments_['particletype'], str):
            if (self.optional_arguments_['particletype'] == 'hadron') or (self.optional_arguments_['particletype'] == 'parton'):
                self.particle_type_ = self.optional_arguments_['particletype']
            else:
                raise ValueError("'particletype' has to be 'hadron' or 'parton'")
        elif 'particletype' in self.optional_arguments_.keys() and not isinstance(self.optional_arguments_['particletype'], str):
            raise TypeError("'particletype' is not given as a string value") 

        if self.particle_type_ == 'hadron':
            self.particle_type_defining_string_ = 'N_hadrons'
        else:
            self.particle_type_defining_string_ = 'N_partons'

        self.set_num_output_per_event()
        return (self.set_particle_list(kwargs),  self.num_events_,self.num_output_per_event_)
    
     # PRIVATE CLASS METHODS
    def _get_num_skip_lines(self):
        """
        Get number of initial lines in Jetscape file that are header or comment
        lines and need to be skipped in order to read the particle output.

        Returns
        -------
        skip_lines : int
            Number of initial lines before data.

        """
        if not self.optional_arguments_ or 'events' not in self.optional_arguments_.keys():
            skip_lines = 1
        elif isinstance(self.optional_arguments_['events'], int):
            if self.optional_arguments_['events'] == 0:
                skip_lines = 1
            else:
                cumulate_lines = 0
                for i in range(0, self.optional_arguments_['events']):
                    cumulate_lines += self.num_output_per_event_[i,1] + 1
                skip_lines = 1 + cumulate_lines
        elif isinstance(self.optional_arguments_['events'], tuple):
            line_start = self.optional_arguments_['events'][0]
            if line_start == 0:
                skip_lines = 1
            else:
                cumulate_lines = 0
                for i in range(0, line_start):
                    cumulate_lines += self.num_output_per_event_[i,1] + 1
                skip_lines = 1 + cumulate_lines
        else:
            raise TypeError('Value given as flag "events" is not of type ' +
                            'int or a tuple of two int values')

        return skip_lines   

    def event_end_lines(self):
        return self.event_end_lines_

    def __get_num_read_lines(self):
        if not self.optional_arguments_ or 'events' not in self.optional_arguments_.keys():
            cumulated_lines = np.sum(self.num_output_per_event_, axis=0)[1]
            # add number of comments
            cumulated_lines += int(len(self.num_output_per_event_))

        elif isinstance(self.optional_arguments_['events'], int):
            read_event = self.optional_arguments_['events']
            cumulated_lines = int(self.num_output_per_event_[read_event][1] + 1)

        elif isinstance(self.optional_arguments_['events'], tuple):
            cumulated_lines = 0
            event_start = self.optional_arguments_['events'][0]
            event_end = self.optional_arguments_['events'][1]
            for i in range(event_start, event_end+1):
                cumulated_lines += int(self.num_output_per_event_[i, 1] + 1)
        else:
            raise TypeError('Value given as flag events is not of type int or a tuple')

        # +1 for the end line in Jetscape format
        return cumulated_lines + 1

    def __apply_kwargs_filters(self, event, filters_dict):
        if not isinstance(filters_dict, dict) or len(filters_dict.keys()) == 0:
            return event
        for i in filters_dict.keys():
            if i == 'charged_particles':
                if filters_dict['charged_particles']:
                    event = charged_particles(event)
            elif i == 'uncharged_particles':
                if filters_dict['uncharged_particles']:
                    event = uncharged_particles(event)
            elif i == 'strange_particles':
                if filters_dict['strange_particles']:
                    event = strange_particles(event)
            elif i == 'particle_species':
                event = particle_species(event, filters_dict['particle_species'])
            elif i == 'remove_particle_species':
                event = remove_particle_species (event, filters_dict['remove_particle_species'])
            elif i == 'lower_event_energy_cut':
                event = lower_event_energy_cut(event, filters_dict['lower_event_energy_cut'])
            elif i == 'pt_cut':
                event = pt_cut(event, filters_dict['pt_cut'])
            elif i == 'rapidity_cut':
                event = rapidity_cut(event, filters_dict['rapidity_cut'])
            elif i == 'pseudorapidity_cut':
                event = pseudorapidity_cut(event, filters_dict['pseudorapidity_cut'])
            elif i == 'spatial_rapidity_cut':
                event = spatial_rapidity_cut(event, filters_dict['spatial_rapidity_cut'])
            elif i == 'multiplicity_cut':
                event = multiplicity_cut(event, filters_dict['multiplicity_cut'])
            elif i == 'particle_status':
                event = particle_status(event, filters_dict['particle_status'])
            else:
                raise ValueError('The cut is unknown!')

        return event

    # PUBLIC CLASS METHODS

    def set_particle_list(self, kwargs):
        particle_list = []
        data = []
        num_read_lines = self.__get_num_read_lines()
        with open(self.PATH_JETSCAPE_, 'r') as jetscape_file:
            self._skip_lines(jetscape_file)
    
            for i in range(0, num_read_lines):
                line = jetscape_file.readline()
                if not line:
                    raise IndexError('Index out of range of JETSCAPE file')
                elif '#' in line and 'sigmaGen' in line:
                    if 'filters' in self.optional_arguments_.keys():
                        data = self.__apply_kwargs_filters([data],kwargs['filters'])[0]
                        self.num_output_per_event_[len(particle_list)]=(len(particle_list)+1,len(data))
                    particle_list.append(data)
                elif i == 0 and '#' not in line and 'weight' not in line:
                    raise ValueError('First line of the event is not a comment ' +
                                     'line or does not contain "weight"')
                elif 'Event' in line and 'weight' in line:
                    line = line.replace('\n','').replace('\t',' ').split(' ')
                    first_event_header = 1
                    if 'events' in self.optional_arguments_.keys():
                        if isinstance(kwargs['events'], int):
                            first_event_header += int(kwargs['events'])
                        else:
                            first_event_header += int(kwargs['events'][0])
                    if int(line[2]) == first_event_header:
                        continue
                    else:
                        if 'filters' in self.optional_arguments_.keys():
                            data = self.__apply_kwargs_filters([data],kwargs['filters'])[0]
                            self.num_output_per_event_[len(particle_list)]=(len(particle_list)+1,len(data))
                        particle_list.append(data)
                        data = []
                else:
                    line = line.replace('\n','').replace('\t',' ').split(' ')
                    particle = Particle("JETSCAPE", line)
                    data.append(particle)

        # Correct num_output_per_event and num_events
        if not kwargs or 'events' not in self.optional_arguments_.keys():
            if len(particle_list) != self.num_events_:
                raise IndexError('Number of events in Jetscape file does not match the '+
                                 'number of events specified by the comments in the '+
                                 'Jetscape file!')
        elif isinstance(kwargs['events'], int):
            update = self.num_output_per_event_[kwargs['events']]
            self.num_output_per_event_ = [update]
            self.num_events_ = int(1)
        elif isinstance(kwargs['events'], tuple):
            event_start = kwargs['events'][0]
            event_end = kwargs['events'][1]
            update = self.num_output_per_event_[event_start : event_end+1]
            self.num_output_per_event_ = update
            self.num_events_ = int(event_end - event_start+1)
        
        return particle_list

    def set_num_output_per_event(self):
        with open(self.PATH_JETSCAPE_, 'r') as jetscape_file:
            event_output = []
    
            while True:
                line = jetscape_file.readline()
                if not line:
                    break
                elif '#' in line and self.particle_type_defining_string_ in line:
                    line_str = line.replace('\n','').replace('\t',' ').split(' ')
                    event = line_str[2]
                    num_output = line_str[8]
                    event_output.append([event, num_output])
                else:
                    continue

        self.num_output_per_event_ = np.asarray(event_output, dtype=np.int32)
        self.num_events_ = len(event_output)

    def get_last_line(self,file_path):
        """
        Returns the last line of a file.

        Parameters
        ----------
        file_path : str
            The path to the file.

        Returns
        -------
        str
            The last line of the file, stripped of leading and trailing whitespace.
        """
        with open(file_path, 'rb') as file:
            file.seek(-2, 2)
            while file.read(1) != b'\n':
                file.seek(-2, 1)
            last_line = file.readline().decode().strip()
            return last_line

    def get_sigmaGen(self):
        """
        Retrieves the sigmaGen values with error from the last line of a file.

        Returns
        -------
        tuple
            A tuple containing the first and second sigmaGen values as floats.
        """
        last_line = self.get_last_line(self.PATH_JETSCAPE_)
        words = last_line.split()
        numbers = []

        for word in words:
            try:
                number = float(word)
                numbers.append(number)
                if len(numbers) == 2:
                    break
            except ValueError:
                continue

        return (numbers[0],numbers[1])
    
    def get_particle_type_defining_string(self):
        """
        Returns the string which definies the particle type in the Jetscape file.

        Returns
        -------
        string
            The particle type defining string.
        """
        return self.particle_type_defining_string_
    
    def get_particle_type(self):
        """
        Returns the particle type of the Jetscape file.

        Returns
        -------
        string
            The particle type.
        """
        return self.particle_type_
        