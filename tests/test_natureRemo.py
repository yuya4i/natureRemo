import pytest
import json
from unittest.mock import Mock, patch
from natureRemo import NatureRemoAPI, DeviceController, AutomationController

@pytest.fixture
def mock_config():
    return {
        'api': {
            'token': 'test_token',
            'base_url': 'https://api.nature.global/1/',
            'local_url': 'http://192.168.1.1/messages'
        },
        'devices': {
            'aircon': {
                'id': 'aircon_id',
                'settings': {
                    'mode': 'cool',
                    'temp': '26',
                    'fan': 'auto'
                }
            },
            'light': {
                'id': 'light_id'
            }
        },
        'schedule': [
            {
                'time': '07:00',
                'action': 'turn_on_light',
                'device': 'light',
                'params': {}
            }
        ],
        'automation': {
            'temperature': {
                'high_threshold': 28,
                'low_threshold': 20,
                'action_high': {
                    'device': 'aircon',
                    'action': 'set_aircon',
                    'params': {
                        'mode': 'cool',
                        'temp': '26',
                        'fan': 'auto'
                    }
                },
                'action_low': {
                    'device': 'aircon',
                    'action': 'turn_off_aircon',
                    'params': {}
                }
            }
        },
        'logging': {
            'level': 'INFO',
            'file': 'test.log',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

@pytest.fixture
def mock_api(mock_config):
    with patch('natureRemo.requests') as mock_requests:
        api = NatureRemoAPI(mock_config)
        yield api, mock_requests

class TestNatureRemoAPI:
    def test_get_devices(self, mock_api):
        api, mock_requests = mock_api
        mock_response = Mock()
        mock_response.json.return_value = {'devices': [{'id': 'test_device'}]}
        mock_requests.get.return_value = mock_response

        result = api.get_devices()
        assert result == {'devices': [{'id': 'test_device'}]}
        mock_requests.get.assert_called_once_with(
            f"{api.base_url}devices",
            headers=api.headers
        )

    def test_control_aircon(self, mock_api):
        api, mock_requests = mock_api
        mock_response = Mock()
        mock_requests.post.return_value = mock_response

        settings = {'mode': 'cool', 'temp': '26'}
        api.control_aircon('device_id', settings)
        
        mock_requests.post.assert_called_once_with(
            f"{api.base_url}appliances/device_id/aircon_settings",
            headers=api.headers,
            data=settings
        )

    def test_control_light(self, mock_api):
        api, mock_requests = mock_api
        mock_response = Mock()
        mock_requests.post.return_value = mock_response

        api.control_light('device_id', True)
        
        mock_requests.post.assert_called_once_with(
            f"{api.base_url}appliances/device_id/light",
            headers=api.headers,
            data={'button': 'on'}
        )

class TestDeviceController:
    @pytest.fixture
    def device_controller(self, mock_config):
        with patch('natureRemo.NatureRemoAPI') as mock_api_class:
            api = mock_api_class.return_value
            controller = DeviceController(api, mock_config)
            yield controller, api

    def test_execute_action_light_on(self, device_controller):
        controller, mock_api = device_controller
        action = {
            'device': 'light',
            'action': 'turn_on_light',
            'params': {}
        }
        
        controller.execute_action(action)
        mock_api.control_light.assert_called_once_with('light_id', True)

    def test_execute_action_aircon(self, device_controller):
        controller, mock_api = device_controller
        action = {
            'device': 'aircon',
            'action': 'set_aircon',
            'params': {
                'mode': 'cool',
                'temp': '26'
            }
        }
        
        controller.execute_action(action)
        mock_api.control_aircon.assert_called_once_with(
            'aircon_id',
            {'mode': 'cool', 'temp': '26'}
        )

class TestAutomationController:
    @pytest.fixture
    def automation_controller(self, mock_config):
        with patch('natureRemo.DeviceController') as mock_device_controller_class:
            device_controller = mock_device_controller_class.return_value
            controller = AutomationController(device_controller, mock_config)
            yield controller, device_controller

    def test_check_sensor_rules_high_temp(self, automation_controller):
        controller, mock_device_controller = automation_controller
        sensor_data = {
            'temperature': '29',
            'humidity': '50'
        }
        
        controller.check_sensor_rules(sensor_data)
        mock_device_controller.execute_action.assert_called_once_with(
            controller.automation_rules['temperature']['action_high']
        )

    def test_check_sensor_rules_low_temp(self, automation_controller):
        controller, mock_device_controller = automation_controller
        sensor_data = {
            'temperature': '19',
            'humidity': '50'
        }
        
        controller.check_sensor_rules(sensor_data)
        mock_device_controller.execute_action.assert_called_once_with(
            controller.automation_rules['temperature']['action_low']
        )

    def test_setup_schedules(self, automation_controller):
        controller, mock_device_controller = automation_controller
        with patch('natureRemo.schedule') as mock_schedule:
            controller.setup_schedules()
            assert mock_schedule.every.return_value.day.at.called
