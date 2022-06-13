# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
###############################################################################
# Copyright (c), The AiiDA-CP2K authors.                                      #
# SPDX-License-Identifier: MIT                                                #
# AiiDA-CP2K is hosted on GitHub at https://github.com/aiidateam/aiida-cp2k   #
# For further information on the license, see the LICENSE.txt file.           #
###############################################################################
"""Run DFT ENERGY calculation for excited state."""

import os
import sys
import click

import ase.io

from aiida.common import NotExistent
from aiida.engine import run
from aiida.orm import (Code, Dict, SinglefileData)
from aiida.plugins import DataFactory

StructureData = DataFactory('structure')  # pylint: disable=invalid-name

def example_excitation(cp2k_code):
    """Run excitation energy calculation."""

    print("Testing CP2K excited state ENERGY on acetylene (DFT-ADMM)...")

    thisdir = os.path.dirname(os.path.realpath(__file__))

    # Structure.
    structure = StructureData(ase=ase.io.read(os.path.join(thisdir, '..', "files", 'acetylene.xyz')))

    # Basis set.
    basis_file_molopt = SinglefileData(file=os.path.join(thisdir, "..", "files", "BASIS_MOLOPT")) 
    basis_file_grb = SinglefileData(file=os.path.join(thisdir, "..", "files", "BASIS_ccGRB_UZH"))
    basis_file_admm = SinglefileData(file=os.path.join(thisdir, "..", "files", "BASIS_ADMM_UZH")) 

    # Pseudopotentials.
    pseudo_file = SinglefileData(file=os.path.join(thisdir, "..", "files", "GTH_POTENTIALS"))

    # Parameters.
    parameters = Dict(
        dict={
            'FORCE_EVAL': {
                'METHOD': 'Quickstep',
                'PROPERTIES' : {
                    'TDDFPT' : {
                        'NSTATES': 2,
                        'MAX_ITER': 50,
                        'CONVERGENCE': '[eV] 1.0e-5',
                        'ADMM_KERNEL_CORRECTION_SYMMETRIC': True,
                    },
                },
                'DFT': {
                    'BASIS_SET_FILE_NAME': ['BASIS_ccGRB_UZH','BASIS_ADMM_UZH'],
                    'POTENTIAL_FILE_NAME': 'POTENTIAL_UZH',
                    'QS': {
                        'EPS_DEFAULT': 1.0e-12,
                        'WF_INTERPOLATION': 'ps',
                        'EXTRAPOLATION_ORDER': 3,
                    },
                    'MGRID': {
                        'CUTOFF': 900,
                        'REL_CUTOFF': 60,
                    }, # try without SCF cycle
                    # ADMM section here
                    'AUXILIARY_DENSITY_MATRIX_METHOD': {
                        'METHOD': 'BASIS_PROJECTION',
                        'ADMM_PURIFICATION_METHOD': 'NONE',
                        'EXCH_SCALING_MODEL': 'NONE',
                        'EXCH_CORRECTION_FUNC': 'NONE',
                    },
                    # EXCITED STATE
                    'EXCITED_STATES': {
                        'STATE': 1,
                    },
                    'XC': {
                        'XC_FUNCTIONAL': {
                            'GGA_C_PBE': {},
                            'GGA_X_PBE': {
                                'SCALE': 0.75,
                            },
                        },
                        'HF': {
                            'FRACTION': 0.25,
                            'HF_INFO': {},
                            'INTERACTION_POTENTIAL': {
                                'POTENTIAL_TYPE': 'TRUNCATED',
                                'CUTOFF_RADIUS': 4.0,
                            },
                            'SCREENING': {
                                'EPS_SCHWARZ': 1.0E-10,
                                'SCREEN_ON_INITIAL_P': False,
                            },
                            'MEMORY': {
                                'MAX_MEMORY': 3000,
                            }
                        },
                    },
                    'POISSON': {
                        'PERIODIC': 'NONE',
                        'PSOLVER': 'WAVELET',
                    },
                },
                'SUBSYS': {
                    'CELL': {
                        'ABC': '14.0 14.0 14.0',
                        'PERIODIC': 'NONE'
                    },
                    'TOPOLOGY': {
                        'CENTER_COORDINATES': {},
                    },
                    'KIND': [
                        {
                            '_': 'H',
                            'BASIS_SET ORB': 'ccGRB-D-q1',
                            'BASIS_SET AUX_FIT': 'admm-dzp-q1',
                            'POTENTIAL': 'GTH-PBE0-q1'
                        },
                        {
                            '_': 'C',
                            'BASIS_SET ORB': 'ccGRB-D-q4',
                            'BASIS_SET AUX_FIT': 'admm-dzp-q4',
                            'POTENTIAL': 'GTH-PBE0-q4'
                        },
                    ],
                },
            }
        })

    # Construct process builder.
    builder = cp2k_code.get_builder()
    builder.structure = structure
    builder.parameters = parameters
    builder.code = cp2k_code
    builder.file = {
        'basis_molopt': basis_file_molopt,
        'basis_grb': basis_file_grb,
        'basis_admm': basis_file_admm,
        'pseudo': pseudo_file,
    }
    builder.metadata.options.resources = {
        "num_machines": 16,
        "num_mpiprocs_per_machine": 1,
    }
    builder.metadata.options.max_wallclock_seconds = 1 * 3 * 60

    print("Submitted calculation...")
    run(builder)


@click.command('cli')
@click.argument('codelabel')
def cli(codelabel):
    """Click interface."""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print(f"The code '{codelabel}' does not exist.")
        sys.exit(1)
    example_excitation(code)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
