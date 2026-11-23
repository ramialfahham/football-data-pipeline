"""The catalogue's metric order for the mock generators: group order, then the metric's order in its group.

A generator names WHICH metrics its page shows; this module says in what order. A metric without a
`metric_order` fails the generator, never gets a position of its own.
"""
import csv
from pathlib import Path

CATALOGUE = Path(__file__).resolve().parent.parent / "dbt_project/seeds/metric_catalogue.csv"
_BY_KEY = {(r["metric_id"], r["entity"]): r for r in csv.DictReader(CATALOGUE.open(encoding="utf-8"))}


def place(metric_id, entity):
    row = _BY_KEY.get((metric_id, entity))
    if row is None or not row["metric_order"]:
        raise SystemExit("FATAL: no %s metric_order in %s for '%s'. A page's order is the catalogue's; "
                         "it is never invented here." % (entity, CATALOGUE.name, metric_id))
    return int(row["metric_group_order"]), int(row["metric_order"])


def in_catalogue_order(metric_ids, entity):
    return sorted(metric_ids, key=lambda m: place(m, entity))


def groups_in_catalogue_order(metric_ids, entity):
    """[("metricGroups.<group>.label", [metric ids in order])] in the catalogue's group order."""
    groups = []
    for metric_id in in_catalogue_order(metric_ids, entity):
        label = "metricGroups.%s.label" % _BY_KEY[(metric_id, entity)]["metric_group"]
        if groups and groups[-1][0] == label:
            groups[-1][1].append(metric_id)
        else:
            groups.append((label, [metric_id]))
    return groups
