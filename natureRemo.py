#!/usr/bin/env python3
import json
import logging
import os
import schedule
import time
import requests
from typing import Dict, Any, Optional
from logging import Logger
from datetime import datetime
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    """環境変数から設定を読み込む"""
    load_dotenv()
    
    return {
        'api': {
            'token': os.getenv('NATURE_REMO_API_TOKEN'),
            'base_url': os.getenv('NATURE_REMO_BASE_URL'),
            'local_url': os.getenv('NATURE_REMO_LOCAL_URL')
        },
        'devices': {
            'aircon': {
                'id': os.getenv('NATURE_REMO_AIRCON_ID'),
                'settings': {
                    'mode': os.getenv('DEFAULT_AIRCON_MODE', 'cool'),
                    'temp': os.getenv('DEFAULT_AIRCON_TEMP', '26'),
                    'fan': os.getenv('DEFAULT_AIRCON_FAN', 'auto')
                }
            },
            'light': {
                'id': os.getenv('NATURE_REMO_LIGHT_ID')
            }
        },
        'automation': {
            'temperature': {
                'high_threshold': float(os.getenv('TEMP_HIGH_THRESHOLD', '28')),
                'low_threshold': float(os.getenv('TEMP_LOW_THRESHOLD', '20')),
                'action_high': {
                    'device': 'aircon',
                    'action': 'set_aircon',
                    'params': {
                        'mode': os.getenv('DEFAULT_AIRCON_MODE', 'cool'),
                        'temp': os.getenv('DEFAULT_AIRCON_TEMP', '26'),
                        'fan': os.getenv('DEFAULT_AIRCON_FAN', 'auto')
                    }
                },
                'action_low': {
                    'device': 'aircon',
                    'action': 'turn_off_aircon',
                    'params': {}
                }
            },
            'humidity': {
                'high_threshold': float(os.getenv('HUMIDITY_HIGH_THRESHOLD', '70')),
                'action': {
                    'device': 'aircon',
                    'action': 'set_aircon',
                    'params': {
                        'mode': 'dry',
                        'fan': 'auto'
                    }
                }
            }
        },
        'schedule': json.loads(os.getenv('SCHEDULE_CONFIG', '[]')),
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': os.getenv('LOG_FILE', 'natureRemo.log'),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }
    }

class NatureRemoAPI:
    """Nature Remo APIとの通信を担当するクラス"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Args:
            config: 設定情報を含む辞書
        """
        if not config['api']['token']:
            raise ValueError("API token is not set in environment variables")
            
        self.token = config['api']['token']
        self.base_url = config['api']['base_url']
        self.local_url = config['api']['local_url']
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.logger = self._setup_logger(config['logging'])

    def _setup_logger(self, log_config: Dict[str, str]) -> Logger:
        """ロギングの設定

        Args:
            log_config: ロギング設定を含む辞書

        Returns:
            Logger: 設定済みのロガーインスタンス
        """
        logger = logging.getLogger('NatureRemo')
        logger.setLevel(log_config['level'])
        
        formatter = jsonlogger.JsonFormatter(log_config['format'])
        
        file_handler = logging.FileHandler(log_config['file'])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger

    def get_devices(self) -> Dict[str, Any]:
        """デバイス一覧の取得

        Returns:
            Dict[str, Any]: デバイス情報を含む辞書
        """
        try:
            response = requests.get(f"{self.base_url}devices", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"デバイス一覧の取得に失敗: {str(e)}")
            raise

    def control_aircon(self, device_id: str, settings: Dict[str, str]) -> None:
        """エアコンの制御

        Args:
            device_id: デバイスID
            settings: 設定値（モード、温度、風量など）
        """
        try:
            endpoint = f"{self.base_url}appliances/{device_id}/aircon_settings"
            response = requests.post(endpoint, headers=self.headers, data=settings)
            response.raise_for_status()
            self.logger.info(f"エアコン制御成功: device_id={device_id}, settings={settings}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"エアコン制御失敗: {str(e)}")
            raise

    def control_light(self, device_id: str, state: bool) -> None:
        """照明の制御

        Args:
            device_id: デバイスID
            state: True=オン、False=オフ
        """
        try:
            endpoint = f"{self.base_url}appliances/{device_id}/light"
            data = {'button': 'on' if state else 'off'}
            response = requests.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            self.logger.info(f"照明制御成功: device_id={device_id}, state={state}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"照明制御失敗: {str(e)}")
            raise

    def get_sensor_data(self, device_id: str) -> Dict[str, Any]:
        """センサーデータの取得

        Args:
            device_id: デバイスID

        Returns:
            Dict[str, Any]: センサー情報を含む辞書
        """
        try:
            response = requests.get(f"{self.base_url}devices/{device_id}/sensor_values", 
                                  headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"センサーデータ取得失敗: {str(e)}")
            raise

class DeviceController:
    """デバイスの制御を担当するクラス"""
    
    def __init__(self, api: NatureRemoAPI, config: Dict[str, Any]) -> None:
        """
        Args:
            api: NatureRemoAPIインスタンス
            config: 設定情報を含む辞書
        """
        self.api = api
        self.config = config
        self.devices = config['devices']
        self.logger = logging.getLogger('DeviceController')

    def execute_action(self, action: Dict[str, Any]) -> None:
        """アクションの実行

        Args:
            action: 実行するアクション情報
        """
        device_type = action['device']
        device_id = self.devices[device_type]['id']
        
        try:
            if action['action'].startswith('turn_on'):
                self.api.control_light(device_id, True)
            elif action['action'].startswith('turn_off'):
                self.api.control_light(device_id, False)
            elif action['action'] == 'set_aircon':
                self.api.control_aircon(device_id, action['params'])
            else:
                self.logger.warning(f"未知のアクション: {action['action']}")
        except Exception as e:
            self.logger.error(f"アクション実行失敗: {str(e)}")
            raise

class AutomationController:
    """自動化制御を担当するクラス"""
    
    def __init__(self, device_controller: DeviceController, config: Dict[str, Any]) -> None:
        """
        Args:
            device_controller: DeviceControllerインスタンス
            config: 設定情報を含む辞書
        """
        self.device_controller = device_controller
        self.automation_rules = config['automation']
        self.schedule_rules = config['schedule']
        self.logger = logging.getLogger('AutomationController')

    def setup_schedules(self) -> None:
        """スケジュールの設定"""
        for rule in self.schedule_rules:
            schedule.every().day.at(rule['time']).do(
                self.device_controller.execute_action, rule
            )
            self.logger.info(f"スケジュール設定: {rule}")

    def check_sensor_rules(self, sensor_data: Dict[str, Any]) -> None:
        """センサーデータに基づくルールのチェックと実行

        Args:
            sensor_data: センサーデータ
        """
        temp = float(sensor_data.get('temperature', 0))
        humidity = float(sensor_data.get('humidity', 0))

        # 温度ルール
        temp_rules = self.automation_rules.get('temperature', {})
        if temp > temp_rules.get('high_threshold', 100):
            self.device_controller.execute_action(temp_rules['action_high'])
        elif temp < temp_rules.get('low_threshold', 0):
            self.device_controller.execute_action(temp_rules['action_low'])

        # 湿度ルール
        humidity_rules = self.automation_rules.get('humidity', {})
        if humidity > humidity_rules.get('high_threshold', 100):
            self.device_controller.execute_action(humidity_rules['action'])

def main():
    """メイン関数"""
    try:
        config = load_config()
    except Exception as e:
        print(f"Error: 設定の読み込みに失敗しました: {str(e)}")
        return

    # 各コントローラーの初期化
    api = NatureRemoAPI(config)
    device_controller = DeviceController(api, config)
    automation_controller = AutomationController(device_controller, config)

    # スケジュールの設定
    automation_controller.setup_schedules()

    # メインループ
    try:
        while True:
            schedule.run_pending()
            
            # センサーデータの取得と自動化ルールの実行
            for device_type, device_info in config['devices'].items():
                try:
                    sensor_data = api.get_sensor_data(device_info['id'])
                    automation_controller.check_sensor_rules(sensor_data)
                except Exception as e:
                    api.logger.error(f"センサーデータ処理エラー: {str(e)}")
            
            time.sleep(60)  # 1分待機
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
    except Exception as e:
        api.logger.error(f"予期せぬエラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()
