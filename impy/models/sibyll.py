'''
Created on 17.03.2014

@author: afedynitch
'''

import numpy as np
from impy.common import MCRun, MCEvent, impy_config
from impy.util import standard_particles, info


class SibyllEvent(MCEvent):
    """Wrapper class around SIBYLL 2.1 & 2.3 particle stack."""
    # Workaround for no data on vertext positions in SIBYLL
    _no_vertex_data = None

    def __init__(self, lib, event_kinematics, event_frame):
        # HEPEVT (style) common block
        evt = lib.hepevt

        # Save selector for implementation of on-demand properties
        px, py, pz, en, m = evt.phep
        vx, vy, vz, vt = evt.vhep

        MCEvent.__init__(self,
                         lib=lib,
                         event_kinematics=event_kinematics,
                         event_frame=event_frame,
                         nevent=evt.nevhep,
                         npart=evt.nhep,
                         p_ids=evt.idhep,
                         status=evt.isthep,
                         px=px,
                         py=py,
                         pz=pz,
                         en=en,
                         m=m,
                         vx=vx,
                         vy=vy,
                         vz=vz,
                         vt=vt,
                         pem_arr=evt.phep,
                         vt_arr=evt.vhep)

    def filter_final_state(self):
        self.selection = np.where(self.status == 1)
        self._apply_slicing()

    def filter_final_state_charged(self):
        self.selection = np.where((self.status == 1) & (self.charge != 0))
        self._apply_slicing()
    
    # def filter_final_state_centrality(self, event_kinematics, centrality_range):
    #     '''Filters all events within the selected centrality bins, defined by the impact parameter and the radius of the nucleus (R = 1.2*A^(1/3)fm; works with error < 1%). This calculation works for all except for peripheral centrality bins (> 50%). 
    #     Source: https://www.hindawi.com/journals/ahep/2013/908046/
    #     This only works for MC models that support NN collisions (that have impact parameter calculations). 
    #     '''
    #     centrality_val = (self.impact_parameter)**2 / (2*1.2*(event_kinematics.A1**(1/3)))**2

    #     self.selection = np.where((self.status == 1) &
    #      (self.charge != 0) & (centrality_val > centrality_range[0]) &(centrality_val < centrality_range[1]))
    #     self._apply_slicing()

    @property
    def charge(self):
        return self.lib.schg.ichg[self.selection]

    @property
    def parents(self):
        #Ask Felix!!!
        pass

    @property
    def children(self):
        pass

    # Nuclear collision parameters
    @property
    def impact_parameter(self):
        """Impact parameter for nuclear collisions."""
        return self.lib.cnucms.b

    @property
    def n_wounded_A(self):
        """Number of wounded nucleons side A"""
        return self.lib.cnucms.na

    @property
    def n_wounded_B(self):
        """Number of wounded nucleons side B"""
        return self.lib.cnucms.nb

    @property
    def n_NN_interactions(self):
        """Number of inelastic nucleon-nucleon interactions"""
        return self.lib.cnucms.ni


class SIBYLLRun(MCRun):
    """Implements all abstract attributes of MCRun for the 
    SIBYLL 2.1, 2.3 and 2.3c event generators."""

    def sigma_inel(self):
        """Inelastic cross section according to current
        event setup (energy, projectile, target)"""
        k = self._curr_event_kin
        sigproj = None
        if abs(k.p1pdg) in [2212, 3112]:
            sigproj = 1
        elif abs(k.p1pdg) == 211:
            sigproj = 2
        elif abs(k.p1pdg) == 321:
            sigproj = 3
        else:
            info(0, "No cross section available for projectile", k.p1pdg)
            raise Exception('Input error')

        return self.lib.sib_sigma_hp(sigproj, self._ecm)[2]

    def sigma_inel_air(self):
        """Inelastic cross section according to current
        event setup (energy, projectile, target)"""
        k = self._curr_event_kin
        sigproj = None
        if abs(k.p1pdg) in [2212, 2112, 3112]:
            sigproj = 1
        elif abs(k.p1pdg) == 211:
            sigproj = 2
        elif abs(k.p1pdg) == 321:
            sigproj = 3
        else:
            info(0, "No cross section available for projectile", k.p1pdg)
            raise Exception('Input error')

        return self.lib.sib_sigma_hair(sigproj, self._ecm)[0]

    def set_event_kinematics(self, event_kinematics):
        """Set new combination of energy, momentum, projectile
        and target combination for next event."""

        info(5, 'Setting event kinematics.')
        info(10, event_kinematics)
        k = event_kinematics

        self._sibproj = self.lib.isib_pdg2pid(k.p1pdg)
        self._iatarg = k.A2
        self._ecm = k.ecm
        self._curr_event_kin = event_kinematics

    def attach_log(self):
        """Routes the output to a file or the stdout."""
        fname = impy_config['output_log']
        if fname == 'stdout':
            self.lib.s_debug.lun = 6
            info(5, 'Output is routed to stdout.')
        else:
            lun = self._attach_fortran_logfile(fname)
            self.lib.s_debug.lun = lun
            info(5, 'Output is routed to', fname, 'via LUN', lun)

    def init_generator(self, event_kinematics, seed='random'):
        from random import randint

        self._abort_if_already_initialized()

        if seed == 'random':
            seed = randint(1000000, 10000000)
        else:
            seed = int(seed)
        info(5, 'Using seed:', seed)

        self.set_event_kinematics(event_kinematics)
        self.attach_log()
        self.lib.sibini(int(seed))
        self.lib.pdg_ini()
        self.conv_hepevt = (self.lib.sibhep1
                            if '21' in self.lib.__name__ else self.lib.sibhep3)
        self._define_default_fs_particles()

    def set_stable(self, pdgid, stable=True):
        sid = abs(self.lib.isib_pdg2pid(pdgid))
        if abs(pdgid) == 311:
            info(1, 'Ignores K0. Use K0L/S 130/310 in final state definition.')
            return
        idb = self.lib.s_csydec.idb
        if sid == 0 or sid > idb.size - 1:
            return
        if stable:
            info(
                5, 'defining as stable particle pdgid/sid = {0}/{1}'.format(
                    pdgid, sid))
            idb[sid - 1] = -np.abs(idb[sid - 1])
        else:
            info(5, 'pdgid/sid = {0}/{1} allowed to decay'.format(pdgid, sid))
            idb[sid - 1] = np.abs(idb[sid - 1])

    def generate_event(self):
        self.lib.sibyll(self._sibproj, self._iatarg, self._ecm)
        self.lib.decsib()
        self.conv_hepevt()
        return 0  # SIBYLL never rejects
