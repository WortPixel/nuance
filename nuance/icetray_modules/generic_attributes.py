'''
Find functions generating generic attributes, like new event id's, or extracting
filter states from the FilterMask, here.
'''
from icecube import dataclasses
from icecube import dataio
from icecube import icetray


def create_event_id(frame):
        '''
        Add unique, ongoing ID to the event header

        Caution: Needs global variable: new_event_id
        '''

        if 'copy' not in sys.modules:
            import copy

        global new_event_id
        header = copy.copy(frame['I3EventHeader'])
        del frame['I3EventHeader']
        header.run_id = new_event_id
        new_event_id = new_event_id + 1
        frame['I3EventHeader'] = header


def create_filter_values(frame):
    '''
    Store FilerMask values regarding DeepCore into doubles so that they're still
    available when i3 files are converted to hdf5.
    '''

    try:
        dc = frame['FilterMask']['DeepCoreFilter_13'].condition_passed
        ext_dc = frame['FilterMask']['DeepCoreFilter_TwoLayerExp_13'].condition_passed

        frame['DC_passed'] = icetray.I3Bool(dc)
        frame['EXT_passed'] = icetray.I3Bool(ext_dc) 
    except:
        print('FilterMask not found.')


def create_primary(frame, primary_name='I3MCPrimary'):
    '''
    Check whether an attribute for the primary particle is existent,
    if not insert itself.
    '''

    # test if Streams=[icetray.I3Frame.Physics] works as well
    if frame.Stop == icetray.I3Frame.Physics:
        if primary_name not in frame:
            try:
                primaries = frame['I3MCTree'].get_primaries()
                # check if particle is neutrino
                # this is important for coincident events
                for particle in primaries:
                    if particle.is_neutrino:
                        primary = particle
                        break
                frame[primary_name] = dataclasses.I3Particle(primary)
                return frame
            except:
                # TODO create list of except frames
                print('I3MCTree primaries not found.')
