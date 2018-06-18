import logging
import threading

from acts.event import event_bus
from acts.event.event_subscription import EventSubscription
from acts.event.subscription_handle import InstanceSubscriptionHandle
from acts.event.subscription_handle import SubscriptionHandle
from acts.event.subscription_handle import StaticSubscriptionHandle


class SubscriptionBundle(object):
    """A class for maintaining a set of EventSubscriptions in the event bus.

    Attributes:
        subscriptions: A dictionary of {EventSubscription: RegistrationID}
    """

    def __init__(self):
        self.subscriptions = {}
        self._subscription_lock = threading.Lock()
        self._registered = False

    @property
    def registered(self):
        """True if this SubscriptionBundle has been registered."""
        return self._registered

    def add(self, event_type, func, event_filter=None,
            order=0):
        """Adds a new Subscription to this SubscriptionBundle.

        If this SubscriptionBundle is registered, the added Subscription will
        also be registered.

        Returns:
            the EventSubscription object created.
        """
        subscription = EventSubscription(event_type, func,
                                         event_filter=event_filter,
                                         order=order)
        return self.add_subscription(subscription)

    def add_subscription(self, subscription):
        """Adds an existing Subscription to the subscription bundle.

        If this SubscriptionBundle is registered, the added subscription will
        also be registered.

        Returns:
            the subscription object.
        """
        registration_id = None
        with self._subscription_lock:
            if self.registered:
                registration_id = event_bus.register_subscription(subscription)

            self.subscriptions[subscription] = registration_id
        return subscription

    def remove_subscription(self, subscription):
        """Removes a subscription from the SubscriptionBundle.

        If the SubscriptionBundle is registered, removing the subscription will
        also unregister it.
        """
        if subscription not in self.subscriptions.keys():
            return False
        with self._subscription_lock:
            if self.registered:
                event_bus.unregister(self.subscriptions[subscription])
            del self.subscriptions[subscription]
        return True

    def register(self):
        """Registers all subscriptions found within this object."""
        if self.registered:
            return
        with self._subscription_lock:
            self._registered = True
            for subscription, registration_id in self.subscriptions.items():
                if registration_id is not None:
                    logging.warning('Registered subscription found in '
                                    'unregistered SubscriptionBundle: %s, %s' %
                                    (subscription, registration_id))
                self.subscriptions[subscription] = (
                    event_bus.register_subscription(subscription))

    def unregister(self):
        """Unregisters all subscriptions managed by this SubscriptionBundle."""
        if not self.registered:
            return
        with self._subscription_lock:
            self._registered = False
            for subscription, registration_id in self.subscriptions.items():
                if registration_id is None:
                    logging.warning('Unregistered subscription found in '
                                    'registered SubscriptionBundle: %s, %s' %
                                    (subscription, registration_id))
                event_bus.unregister(subscription)
                self.subscriptions[subscription] = None


def create_from_static(obj):
    """Generates a SubscriptionBundle from @subscribe_static functions on obj.

    Args:
        obj: The object that contains @subscribe_static functions. Can either
             be a module or a class.

    Returns:
        An unregistered SubscriptionBundle.
    """
    return _create_from_object(obj, StaticSubscriptionHandle)


def create_from_object(obj):
    """Generates a SubscriptionBundle from @subscribe.* functions on obj.

    Args:
        obj: The object that contains @subscribe.* functions.

    Returns:
        An unregistered SubscriptionBundle.
    """
    return _create_from_object(obj, SubscriptionHandle)


def create_from_instance(instance):
    """Generates a SubscriptionBundle from an instance's @subscribe functions.

    Args:
        instance: The instance object that contains @subscribe functions.

    Returns:
        An unregistered SubscriptionBundle.
    """
    return _create_from_object(instance, InstanceSubscriptionHandle)


def _create_from_object(obj, subscription_handle_type):
    """Generates a SubscriptionBundle from an object's SubscriptionHandles.

    Args:
        obj: The object that contains SubscriptionHandles
        subscription_handle_type: The type of the SubscriptionHandles to
                                  capture.

    Returns:
        An unregistered SubscriptionBundle.
    """
    bundle = SubscriptionBundle()
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name)
        if isinstance(attr, subscription_handle_type):
            # Adds self to the list of arguments
            bundle.add_subscription(attr.subscription)
    return bundle
