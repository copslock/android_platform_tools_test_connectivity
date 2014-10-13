#!/usr/bin/python3.4
#
#   Copyright 2014- The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from concurrent.futures import ThreadPoolExecutor
import logging
import queue
import threading
import time

class EventDispatcherError(Exception):
    pass

class IllegalStateError(EventDispatcherError):
    """Raise when user tries to put event_dispatcher into an illegal state.
    """

class DuplicateError(EventDispatcherError):
    """Raise when a duplicate is being created and it shouldn't.
    """

class EventDispatcher:
    """Class managing events for an sl4a connection.
    """
    def __init__(self, droid):
        self.droid = droid
        self.started = False
        self.executor = None
        self.poller = None
        self.event_dict = {}
        self.handlers = {}

    def poll_events(self):
        """Continuously polls all types of events from sl4a.

        Events are sorted by name and store in separate queues.
        If there are registered handlers, the handlers will be called with
        corresponding event immediately upon event discovery, and the event
        won't be stored. If exceptions occur, stop the dispatcher and return
        """
        try:
            while self.started:
                event_obj = self.droid.eventWait()
                event_name = event_obj['name']
                logging.debug("Polled " + event_name)
                # if handler registered, process event
                if event_name in self.handlers:
                    logging.debug("Handling subscribed event: " + event_name)
                    self.handle_subscribed_event(event_obj, event_name)
                elif event_name in self.event_dict: #otherwise, cache event
                    self.event_dict[event_name].put(event_obj)
                else:
                    q = queue.Queue()
                    q.put(event_obj)
                    self.event_dict[event_name] = q
        except Exception as e:
            # Ignore this exception if it came from terminate.
            if str(e) != "java.lang.InterruptedException":
                logging.error("Exception in polling: " + str(e))
                self.stop()

    def register_handler(self, handler, event_name, args):
        """Registers an event handler.

        One type of event can only have one event handler associated with it.

        Args:
            handler: The event handler function to be registered.
            event_name: Name of the event the handler is for.
            args: User arguments to be passed to the handler when it's called.

        Raises:
            IllegalStateError: Raised if attempts to register a handler after
                the dispatcher starts running.
            DuplicateError: Raised if attempts to register more than one
                handler for one type of event.
        """
        if self.started:
            raise IllegalStateError(("Can't register service after polling is"
                " started"))
        if event_name in self.handlers:
            raise DuplicateError(' '.join(("A handler for", event_name,
                "already exists")))
        self.handlers[event_name] = (handler, args)

    def start(self):
        """Starts the event dispatcher.

        Initiates executor and start polling events.

        Raises:
            IllegalStateError: Can't start a dispatcher again when it's already
                running.
        """
        if not self.started:
            self.started = True
            self.executor = ThreadPoolExecutor(max_workers = 15)
            self.poller = self.executor.submit(self.poll_events)
        else:
            raise IllegalStateError("Dispatcher is already started.")

    def stop(self):
        """Stops the event dispatcher.

        Shuts down the executor, tries to stop polling, and discards unhandled
            events.
        """
        if not self.started:
            return
        logging.debug("stop ed")
        self.started = False
        self.poller.set_result("Done")
        self.executor.shutdown(False)
        self.event_dict.clear()

    def pop_event(self, event_name, timeout=60):
        """Pop an event from its queue.

        Return and remove the oldest entry of an event.
        Block until an event of specified name is available or
        times out if timeout is set.

        Args:
            event_name: Name of the event to be popped.
            timeout: Number of seconds to wait when event is not present.
                Never times out if None.

        Returns:
            event: The oldest entry of the specified event. None if timed out.

        Raises:
            IllegalStateError: Raised if pop is called before the dispatcher
                starts polling.
        """
        if not self.started:
            raise IllegalStateError((("Dispatcher needs to be started before "
                "popping.")))
        e_queue = self.get_event_q(event_name, timeout)
        if not e_queue:
            return None
        return e_queue.get(True, timeout)

    def wait_for_event(self, event_name, predicate, timeout=60):
        """Wait for an event that satisfies a predicate to appear.

        Continuously pop events of a particular name and check against the
        predicate until an event that satisfies the predicate is popped or
        timed out. Note this will remove all the events of the same name that
        do not satisfy the predicate in the process.

        Args:
            event_name: Name of the event to be popped.
            predicate: A function that takes an event and returns True if the
                predicate is satisfied, False otherwise.
            timeout: Number of seconds to wait.

        Returns:
            The event that satisfies the predicate.

        Raises:
            queue.Empty: Raised if no event that satisfies the predicate was
                found before time out.
        """
        deadline = time.time() + timeout
        while True:
            event = self.pop_event(event_name, 1)
            if predicate(event):
                return event
            if time.time() > deadline:
                raise queue.Empty(''.join(("No event '", event_name,
                    "' that satisfies the specified predicate occured.")))

    def pop_events(self, partial_event_name, timeout):
        """Pop events whose names contain partial_event_name.

        If such event(s) exist, pop one event from each event queue that
        satisfies the condition. Otherwise, wait for an event that satisfies
        the condition to occur, with timeout.

        Args:
            partial_event_name: The substring an event's name should contain in
                order to be popped.
            timeout: Number of seconds to wait for events in case no event
                matching the condition exits when the function is called.

        Returns:
            results: Events whose names contain the partial_event_name. Empty
                if none exist and the wait timed out.

        Raises:
            IllegalStateError: Raised if pop is called before the dispatcher
                starts polling.
            queue.Empty: Raised if no event was found before time out.
        """
        if not self.started:
            raise IllegalStateError(("Dispatcher needs to be started before "
                "popping."))
        deadline = time.time() + timeout
        while True:
            results = self._match_and_pop(partial_event_name)
            if len(results) != 0 or time.time() > deadline:
                break
            time.sleep(1)
        if len(results) == 0:
            raise queue.Empty(' '.join(("No event whose name matches '",
                partial_event_name, "'ever occured.")))
        return results

    def _match_and_pop(self, partial_event_name):
        """Pop one event from each of the event queues whose names contain
        partial_event_name, case insensitive.
        """
        results = []
        existing_names = self.event_dict.keys()
        partial_event_name = partial_event_name.lower()
        for name in existing_names:
            if partial_event_name in name.lower():
                q = self.event_dict[name]
                if q:
                    try:
                        results.append(q.get(False))
                    except:
                        pass
        return results

    def get_event_q(self, event_name, timeout=60):
        """Obtain the queue storing events of the specified name.

        If no event of this name has been polled, wait for one to.

        Returns:
            queue: A queue storing all the events of the specified name.
                None if timed out.
            timeout: Number of seconds to wait for the operation.

        Raises:
            queue.Empty: Raised if the queue does not exist and timeout has
                passed.
        """
        deadline = None
        if timeout:
            deadline = time.time() + timeout
        while event_name not in self.event_dict:
            if deadline and time.time() > deadline:
                raise queue.Empty(' '.join(("Timeout: no", event_name,
                    "event ever occured.")))
        return self.event_dict[event_name]

    def handle_subscribed_event(self, event_obj, event_name):
        """Execute the registered handler of an event.

        Retrieve the handler and its arguments, and execute the handler in a
            new thread.

        Args:
            event_obj: Json object of the event.
            event_name: Name of the event to call handler for.
        """
        handler,args = self.handlers[event_name]
        self.executor.submit(handler, event_obj, *args)


    def _handle(self, event_handler, event_name, user_args, event_timeout,
        cond, cond_timeout):
        """Pop an event of specified type and calls its handler on it. If
        condition is not None, block until condition is met or timeout.
        """
        if cond:
            cond.wait(cond_timeout)
        event = self.pop_event(event_name, event_timeout)
        return event_handler(event,*user_args)

    def handle_event(self, event_handler, event_name, user_args,
        event_timeout=None, cond=None, cond_timeout=None):
        """Handle events that don't have registered handlers

        In a new thread, poll one event of specified type from its queue and
        execute its handler. If no such event exists, the thread waits until
        one appears.

        Args:
            event_handler: Handler for the event, which should take at least
                one argument - the event json object.
            event_name: Name of the event to be handled.
            user_args: User arguments for the handler; to be passed in after
                the event json.
            event_timeout: Number of seconds to wait for the event to come.
            cond: A condition to wait on before executing the handler. Should
                be a threading.Event object.
            cond_timeout: Number of seconds to wait before the condition times
                out. Never times out if None.

        Returns:
            worker: A concurrent.Future object associated with the handler.
                If blocking call worker.result() is triggered, the handler
                needs to return something to unblock.
        """
        worker = self.executor.submit(self._handle, event_handler, event_name,
            user_args, event_timeout, cond, cond_timeout)
        return worker

    def pop_all(self, event_name):
        """Return and remove all stored events of a specified name.

        Pops all events from their queue. May miss the latest ones.
        If no event is available, return immediately.

        Args:
            event_name: Name of the events to be popped.

        Returns:
           results: List of the desired events.

        Raises:
            IllegalStateError: Raised if pop is called before the dispatcher
                starts polling.
        """
        if not self.started:
            raise IllegalStateError(("Dispatcher needs to be started before "
                "popping."))
        results = []
        try:
            while True:
                results.append(self.event_dict[event_name].get())
        except (Empty, KeyError):
            return results

    def clear_events(event_name):
        """Clear all events of a particular name.

        Args:
            event_name: Name of the events to be popped.
        """
        try:
            q = self.get_event_q(event_name, 0)
            q.queue.clear()
        except Empty:
            return

    def clear_all_events(self):
        """Clear all event queues and their cached events."""
        self.event_dict.clear()
