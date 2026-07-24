"""Safety guard for integrations that must never mutate Zabbix."""

READ_ONLY_METHODS = frozenset(
    {
        "event.get",
        "graph.get",
        "history.get",
        "host.get",
        "hostgroup.get",
        "item.get",
        "problem.get",
        "trend.get",
        "trigger.get",
    }
)


def ensure_read_only(method: str) -> str:
    """Return a validated method or fail closed for any unknown operation."""
    normalized = method.strip()
    if normalized not in READ_ONLY_METHODS:
        raise PermissionError(f"Zabbix method is not allowed in read-only mode: {normalized}")
    return normalized
