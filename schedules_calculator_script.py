#!/usr/bin/env python3
"""
CronJob Schedule Calculator for OpenShift

This script fetches CronJob schedules from OpenShift clusters and parses
Renovate configuration to extract manager schedules. It calculates the
next N scheduled runs for each and writes results to txt files.

Usage:
    python schedules_calculator_script.py -n 5 -c renovate.json
"""

import subprocess
import argparse
import sys
import logging
import json
from datetime import datetime, timezone
from cron_converter import Cron

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

CRONJOB_NAME = "create-dependencyupdatecheck"
CRONJOB_NAMESPACE = "mintmaker"

def get_cronjob_schedule_from_oc(cronjob_name, namespace=CRONJOB_NAMESPACE):
    try:
        result = subprocess.run([
            "oc", "get", "cronjob", cronjob_name,
            "-n", namespace,
            "-o", "jsonpath={.spec.schedule}"
        ], capture_output=True, text=True, check=True)

        schedule = result.stdout.strip()
        logger.info("Found schedule: %s.", schedule)
        return schedule

    except Exception as e:
        logger.error("Error fetching schedule: %s.", e)
        return None


def merge_cron_schedules(cron_expression, general_schedule_expression):
    """Merge two cron expressions by intersecting their fields."""
    cron = Cron()
    cron.from_string(cron_expression)

    if cron_expression == general_schedule_expression:
        return cron

    general_cron = Cron()
    general_cron.from_string(general_schedule_expression)

    cron_list = cron.to_list()
    general_list = general_cron.to_list()

    field_names = ["minutes", "hours", "days of month", "months", "days of week"]
    merged = []
    for i in range(len(field_names)):
        intersection = sorted(set(cron_list[i]) & set(general_list[i]))
        if not intersection:
            logger.warning("No intersection in %s field - schedules never align.", field_names[i])
            return None
        merged.append(intersection)

    merged_cron = Cron()
    merged_cron.from_list(merged)
    return merged_cron


def analyze_cron_schedule(cron_expression, general_schedule_expression, number_of_runs):
    logger.info("Finding next %d aligned runs between schedules.", number_of_runs)

    merged_schedule = merge_cron_schedules(cron_expression, general_schedule_expression)

    if merged_schedule is None:
        logger.warning("Schedules have no overlap - they never align.")
        return []

    logger.info("Merged schedule: %s", merged_schedule.to_string())

    reference = datetime.now(timezone.utc)
    schedule = merged_schedule.schedule(reference)

    next_runs = []
    for _ in range(number_of_runs):
        next_runs.append(schedule.next().isoformat(timespec="seconds"))

    return next_runs


def write_to_txt(next_runs, filename="scheduled_times.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as output_file:
            for time in next_runs:
                output_file.write(f"{time}\n")
        logger.info("Results written to %s.", filename)
        return True

    except Exception as e:
        logger.error("Could not write to file %s: %s.", filename, e)
        return False


def find_managers_with_schedules(config):
    managers = {}
    enabled_managers = config.get("enabledManagers", [])

    for manager in enabled_managers:
        if manager in config and isinstance(config[manager], dict):
            manager_config = config[manager]
            if "schedule" in manager_config:
                schedule = manager_config["schedule"]
                if isinstance(schedule, list) and schedule:
                    managers[manager] = schedule[0]
                    logger.info("Found manager '%s' with schedule: %s.", manager, schedule[0])

    return managers


def parse_renovate_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        managers_with_schedules = find_managers_with_schedules(config)

        if managers_with_schedules:
            logger.info("Found %d manager(s) with schedules.", len(managers_with_schedules))
        else:
            logger.info("No managers with schedules found.")

        return managers_with_schedules

    except Exception as e:
        logger.error("Error parsing renovate config: %s.", e)
        return {}


def main():
    try:
        parser = argparse.ArgumentParser(description="Analyze CronJob and Renovate managers schedules.")
        parser.add_argument("-n", "--count", type=int, default=5,
                            help="Number of next scheduled runs to calculate (default: 5)")
        parser.add_argument("-c", "--config", type=str, default="renovate.json",
                            help="Config path for renovate.json")
        args = parser.parse_args()

        logger.info("Processing OpenShift CronJob...")
        general_schedule = get_cronjob_schedule_from_oc(CRONJOB_NAME)
        if not general_schedule:
            return 1

        try:
            result = analyze_cron_schedule(general_schedule, general_schedule, args.count)
            write_to_txt(result, "general_scheduled_times.txt")
        except Exception as e:
            logger.error("Failed to process general schedule: %s.", e)

        logger.info("Processing Renovate managers...")
        managers = parse_renovate_config(args.config)

        for manager_name, schedule in managers.items():
            logger.info("Processing manager: %s.", manager_name)

            try:
                result = analyze_cron_schedule(schedule, general_schedule, args.count)
                safe_name = manager_name.replace(".", "_").replace("-", "_")
                filename = f"{safe_name}_scheduled_times.txt"
                write_to_txt(result, filename)

            except Exception as e:
                logger.error("Failed to process manager '%s': %s.", manager_name, e)

        logger.info("Schedule analysis complete.")
        return 0

    except Exception as e:
        logger.error("Error while analyzing schedules: %s.", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())

