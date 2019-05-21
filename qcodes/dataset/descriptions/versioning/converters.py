from typing import Dict, List

from qcodes.dataset.descriptions.param_spec import ParamSpec, ParamSpecBase
from qcodes.dataset.descriptions.dependencies import InterDependencies_
from qcodes.dataset.descriptions.versioning.v0 import InterDependencies


def old_to_new(idps: InterDependencies) -> InterDependencies_:
    """
    Create a new InterDependencies_ object (new style) from an existing
    InterDependencies object (old style). Leaves the original object unchanged.
    Incidentally, this function can serve as a validator of the original object
    """
    namedict: Dict[str, ParamSpec] = {ps.name: ps for ps in idps.paramspecs}

    dependencies = {}
    inferences = {}
    standalones_mut = []
    root_paramspecs: List[ParamSpecBase] = []

    for ps in idps.paramspecs:
        deps = tuple(namedict[n].base_version() for n in ps.depends_on_)
        inffs = tuple(namedict[n].base_version() for n in ps.inferred_from_)
        if len(deps) > 0:
            dependencies.update({ps.base_version(): deps})
            root_paramspecs += list(deps)
        if len(inffs) > 0:
            inferences.update({ps.base_version(): inffs})
            root_paramspecs += list(inffs)
        if len(deps) == len(inffs) == 0:
            standalones_mut.append(ps.base_version())

    standalones = tuple(set(standalones_mut).difference(set(root_paramspecs)))

    idps_ = InterDependencies_(dependencies=dependencies,
                               inferences=inferences,
                               standalones=standalones)
    return idps_


def new_to_old(idps: InterDependencies_) -> InterDependencies:
    """
    Create a new InterDependencies object (old style) from an existing
    InterDependencies_ object (new style). Leaves the original object
    unchanged. Only meant to be used for ensuring backwards-compatibility
    until we update sqlite_base to forget about ParamSpecs
    """

    paramspecs: Dict[str, ParamSpec] = {}

    # first the independent parameters
    for indeps in idps.dependencies.values():
        for indep in indeps:
            paramspecs.update({indep.name: ParamSpec(name=indep.name,
                                                     paramtype=indep.type,
                                                     label=indep.label,
                                                     unit=indep.unit)})

    for inffs in idps.inferences.values():
        for inff in inffs:
            paramspecs.update({inff.name: ParamSpec(name=inff.name,
                                                     paramtype=inff.type,
                                                     label=inff.label,
                                                     unit=inff.unit)})

    for ps_base in idps._paramspec_to_id.keys():
        paramspecs.update({ps_base.name: ParamSpec(name=ps_base.name,
                                                   paramtype=ps_base.type,
                                                   label=ps_base.label,
                                                   unit=ps_base.unit)})

    for ps, indeps in idps.dependencies.items():
        for indep in indeps:
            paramspecs[ps.name]._depends_on.append(indep.name)
    for ps, inffs in idps.inferences.items():
        for inff in inffs:
            paramspecs[ps.name]._inferred_from.append(inff.name)

    return InterDependencies(*tuple(paramspecs.values()))
