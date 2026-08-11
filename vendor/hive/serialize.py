import dataclasses
import json
from typing import Any

_serializers = {}


def register_serializer(type_, to_dict, from_dict):
    _serializers[type_.__name__] = (type_, to_dict, from_dict)


def _serialize_component(obj: Any) -> dict[str, Any]:
    tname = type(obj).__name__
    if dataclasses.is_dataclass(obj):
        return {"__type__": tname, "data": dataclasses.asdict(obj)}
    if tname in _serializers:
        to_dict = _serializers[tname][1]
        return {"__type__": tname, "data": to_dict(obj)}
    # fallback to __dict__ if possible
    if hasattr(obj, "__dict__"):
        return {"__type__": tname, "data": dict(obj.__dict__)}
    raise TypeError(f"No serializer for component type {tname}")


def _deserialize_component(obj: Any) -> dict[str, Any]:
    tname = obj["__type__"]
    data = obj["data"]
    if tname in _serializers:
        from_dict = _serializers[tname][2]
        return from_dict(data)
    # Best-effort: if no custom serializer, assume dataclass and try to
    # reconstruct by finding a class with matching name in the global scope.
    # Try to find the class in module globals first, then in builtins
    cls = globals().get(tname)
    if cls is None:
        # try to locate class in loaded modules
        import sys

        for mod in list(sys.modules.values()):
            if not mod:
                continue
            c = getattr(mod, tname, None)
            if c is not None:
                cls = c
                break
    if cls is not None and dataclasses.is_dataclass(cls):
        return cls(**data)
    raise TypeError(f"No deserializer for component type {tname}")


def snapshot(world) -> dict[str, Any]:
    """Return a JSON-serializable snapshot of the world's components and next id."""
    payload = {
        "next_id": world.store._next_id,
        "components": {},
    }
    for t, cmap in world.store._components.items():
        arr = {}
        for eid, comp in cmap.items():
            arr[str(eid)] = _serialize_component(comp)
        payload["components"][t.__name__] = arr
    # include resources when serializable (dataclasses or registered)
    resources = {}
    for k, v in world.resources.all().items():
        try:
            resources[str(k)] = _serialize_component(v)
        except TypeError:
            # skip non-serializable resources
            pass
    payload["resources"] = resources
    return payload


def load_into_world(snapshot_obj, world) -> None:
    """Load snapshot into an existing World instance.

    Requires that component types referenced in the snapshot are available
    to the runtime (and registered with serializers if not dataclasses).
    """
    world.store._next_id = snapshot_obj.get("next_id", world.store._next_id)
    comps = snapshot_obj.get("components", {})
    # map type name to actual class by searching globals and world scope
    for tname, mapping in comps.items():
        for sid, serialized in mapping.items():
            eid = int(sid)
            comp = _deserialize_component(serialized)
            world.store._components.setdefault(type(comp), {})[eid] = comp
    # resources
    for k, serialized in snapshot_obj.get("resources", {}).items():
        try:
            res = _deserialize_component(serialized)
            world.resources.register(res)
        except TypeError:
            pass


def dump_to_json(snapshot_obj, fp) -> None:
    json.dump(snapshot_obj, fp)
