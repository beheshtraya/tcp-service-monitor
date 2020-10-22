import unittest
from datetime import datetime, timedelta
from unittest.async_case import IsolatedAsyncioTestCase

from main import ServiceList, Service, ServiceMonitor


def void():
    pass


class TestService(unittest.TestCase):
    counter = 0

    def up_callback(self):
        self.counter += 1

    def down_callback(self):
        self.counter -= 1

    def test_is_planned_outage(self):
        s = Service(
            host='127.0.0.1',
            port=9008,
            down_callback=void,
            up_callback=void,
            polling_frequency=1,
            outage_start_time=datetime.now(),
            outage_end_time=datetime.now() + timedelta(minutes=1),
        )

        self.assertTrue(s.is_planned_outage())

        s = Service(
            host='127.0.0.1',
            port=9008,
            down_callback=void,
            up_callback=void,
            polling_frequency=1,
            outage_start_time=datetime.now() + timedelta(hours=1),
            outage_end_time=datetime.now() + timedelta(hours=2),
        )

        self.assertFalse(s.is_planned_outage())

    def test_notify_service_down(self):
        self.counter = 0

        s = Service(
            host='127.0.0.1',
            port=9008,
            down_callback=self.down_callback,
            up_callback=self.up_callback,
            polling_frequency=1,
        )

        s.notify_service_down()
        self.assertEqual(self.counter, -1)

    def test_initial_notify_service_up(self):
        """
        Ensure up_callback does not send notification at first run.
        :return:
        """
        self.counter = 0

        s = Service(
            host='127.0.0.1',
            port=9008,
            down_callback=self.down_callback,
            up_callback=self.up_callback,
            polling_frequency=1,
        )

        s.notify_service_up()
        self.assertEqual(self.counter, 0)

    def test_multiple_notify_service_down(self):
        """
        Ensure only the first service down notification is sent when the service is down in multiple check iteration
        :return:
        """
        self.counter = 0

        s = Service(
            host='127.0.0.1',
            port=9008,
            down_callback=self.down_callback,
            up_callback=self.up_callback,
            polling_frequency=1,
        )

        s.notify_service_down()
        s.notify_service_down()
        s.notify_service_down()
        self.assertEqual(self.counter, -1)


class TestServiceList(unittest.TestCase):
    def test_duplicate_services(self):
        service_list = ServiceList()
        service_list.append(Service('127.0.0.1', 8989, void, void))
        service_list.append(Service('127.0.0.1', 8989, void, void))
        service_list.append(Service('127.0.0.1', 8989, void, void))

        self.assertEqual(len(service_list), 1)

    def test_minimum_polling_frequency(self):
        service_list = ServiceList()
        service_list.append(Service('127.0.0.1', 8989, void, void, 10))
        service_list.append(Service('127.0.0.1', 8989, void, void, 5))
        service_list.append(Service('127.0.0.1', 8989, void, void, 20))

        self.assertEqual(service_list[0].polling_frequency, 5)

    def test_callback_list(self):
        service_list = ServiceList()
        service_list.append(Service('127.0.0.1', 8989, lambda: print('callback func 1'), void))
        service_list.append(Service('127.0.0.1', 8989, lambda: print('callback func 2'), void))
        service_list.append(Service('127.0.0.1', 8989, lambda: print('callback func 3'), void))

        self.assertEqual(len(service_list[0].down_callback_list), 3)


class TestServiceMonitorUp(IsolatedAsyncioTestCase):
    async def test_failed_status(self):
        service_monitor = ServiceMonitor(grace_time=10, verbose=False)
        service = Service('example.com', 80, void, void, 2)
        result = await service_monitor.check_status(service)
        self.assertTrue(result)


class TestServiceMonitorDownBeforeGraceTime(IsolatedAsyncioTestCase):
    async def test_failed_status(self):
        service_monitor = ServiceMonitor(grace_time=10, verbose=False)
        service = Service('127.0.0.1', 65432, void, void, 1)
        result = await service_monitor.check_status(service)
        self.assertIsNone(result)


class TestServiceMonitorDownAfterGraceTime(IsolatedAsyncioTestCase):
    async def test_failed_status(self):
        service_monitor = ServiceMonitor(grace_time=1, verbose=False)
        service = Service('127.0.0.1', 65432, void, void, 2)
        result = await service_monitor.check_status(service)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
