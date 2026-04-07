import logging

logger = logging.getLogger(__name__)


def load_kube_batch_client():
    """
    Returns a configured kubernetes BatchV1Api client.

    Prefers in-cluster config, falls back to local kubeconfig.
    """
    try:
        from kubernetes import client, config  # type: ignore[import-not-found]
        from kubernetes.config.config_exception import (  # type: ignore[import-not-found]
            ConfigException,
        )
    except ImportError as e:
        logger.error("Kubernetes client library is not installed: %s.", e)
        return None

    try:
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config.")
        except ConfigException:
            config.load_kube_config()
            logger.info("Loaded kubeconfig from local environment.")
            
        return client.BatchV1Api()

    except Exception as e:
        logger.error("Failed to load Kubernetes config: %s.", e)
        return None


def get_cronjob_schedule_from_k8s(cronjob_name: str, namespace: str) -> str | None:
    api = load_kube_batch_client()
    if api is None:
        return None

    try:
        cronjob = api.read_namespaced_cron_job(name=cronjob_name, namespace=namespace)
        schedule = getattr(getattr(cronjob, "spec", None), "schedule", None)
        if not schedule:
            logger.error("CronJob %s/%s has no schedule.", namespace, cronjob_name)
            return None
        logger.info("Found schedule: %s.", schedule)
        return schedule
    except Exception as e:
        logger.error("Error fetching CronJob %s/%s: %s.", namespace, cronjob_name, e)
        return None

