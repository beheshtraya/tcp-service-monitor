import asyncio
import socket
from datetime import datetime, timedelta


class Service:
    host = str()
    port = str()
    polling_frequency = int()
    up_callback_list = []
    down_callback_list = []
    outage_start_time = None
    outage_end_time = None
    was_down = False
    down_time = 0
    client = None

    def __init__(self, host, port, down_callback, up_callback, polling_frequency=1,
                 outage_start_time=None, outage_end_time=None):

        self.host = host
        self.port = port
        self.down_callback_list = [down_callback]
        self.up_callback_list = [up_callback]
        self.polling_frequency = max(polling_frequency, 1)  # polling frequency cannot be less than 1
        self.outage_start_time = outage_start_time
        self.outage_end_time = outage_end_time

    def __str__(self):
        return '{}:{}'.format(self.host, self.port)

    def add_callback(self, down_callback, up_callback):
        self.down_callback_list.append(down_callback)
        self.up_callback_list.append(up_callback)

    def set_polling_frequency(self, new_polling_frequency):
        """
        Polling frequency will be changed if the new value is lower than the current value.
        If the value is less than 1, polling value is set to 1.
        :param new_polling_frequency:
        :return:
        """
        self.polling_frequency = min(self.polling_frequency, new_polling_frequency)
        self.polling_frequency = max(self.polling_frequency, 1)

    def notify_service_down(self):
        if not self.was_down:
            for callback in self.down_callback_list:
                callback()

            self.was_down = True

    def notify_service_up(self):
        if self.was_down:
            for callback in self.up_callback_list:
                callback()

            self.was_down = False

    def is_planned_outage(self):
        if not self.outage_start_time or not self.outage_end_time:
            return False

        return self.outage_start_time < datetime.now() < self.outage_end_time

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.close()

    def close(self):
        self.client.close()


class ServiceList(list):
    def append(self, service):
        """
        Override append method to achieve three goals:
            1- avoid registering duplicate services.
            2- set polling frequency to the minimum value when there are multiple registration for a service.
            3- add the new callback to the service callback list if service is already registered.
        :param service:
        :return:
        """
        for item in self.__iter__():
            if str(item) == str(service):
                i = self.index(item)
                self.__getitem__(i).set_polling_frequency(service.polling_frequency)
                self.__getitem__(i).add_callback(service.down_callback_list[0], service.up_callback_list[0])
                return

        super(ServiceList, self).append(service)


class ServiceMonitor:
    service_list = ServiceList()
    verbose = False

    def __init__(self, grace_time=1, verbose=False):
        self.grace_time = grace_time
        self.verbose = verbose

    def print(self, *args):
        if self.verbose:
            print(*args)

    def start(self):
        asyncio.run(self.forever())

    def register(self, host, port, down_callback, up_callback, polling_frequency=1,
                 outage_start_time=None, outage_end_time=None):

        self.service_list.append(
            Service(host, port, down_callback, up_callback, polling_frequency, outage_start_time, outage_end_time))

    async def check_status(self, service):
        """
        :param service:
        :return: True if service is up
                 False if service is down and grace time is reached
                 None  if service is down but grace time is not reached
        """
        if service.is_planned_outage():
            await asyncio.sleep(service.polling_frequency)
            return

        self.print('checking {}'.format(service))
        try:
            service.connect()
            service.notify_service_up()
            service.down_time = 0
            self.print('ok')
            await asyncio.sleep(service.polling_frequency)
            return True

        except ConnectionRefusedError:
            service.down_time += service.polling_frequency

            self.print('fail')

            if service.down_time > self.grace_time:
                service.notify_service_down()
                await asyncio.sleep(min(service.polling_frequency, self.grace_time))
                return False

            # If the grace time is less than the polling frequency,
            # the monitor should schedule extra checks of the service.
            await asyncio.sleep(min(service.polling_frequency, self.grace_time))
            service.close()
            return

    async def check_status_loop(self, service):
        while True:
            await self.check_status(service)

    async def forever(self):
        await asyncio.gather(
            *[self.check_status_loop(service) for service in self.service_list]
        )


if __name__ == '__main__':
    s = ServiceMonitor(grace_time=10, verbose=True)

    # Test basic functionality
    s.register(
        host='127.0.0.1',
        port=9008,
        down_callback=lambda: print('Service went down'),
        up_callback=lambda: print('Service went up'),
        polling_frequency=1
    )

    # Test grace time
    s.register(
        host='127.0.0.1',
        port=9008,
        down_callback=lambda: print('Service went down'),
        up_callback=lambda: print('Service went up'),
        polling_frequency=1,
        outage_start_time=datetime.now(),
        outage_end_time=datetime.now() + timedelta(minutes=1),
    )


    def send_email():
        # this will send an email to notify about service outage
        pass


    # Test with an external service
    s.register('example.com', 80, send_email, send_email, 10)

    s.start()
