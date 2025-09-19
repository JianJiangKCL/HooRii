/**
 * Smart Home API Adapter for Hoorii n8n
 * 预留接口，支持多种智能家居协议
 */

class SmartHomeAdapter {
  constructor(config = {}) {
    this.config = {
      // 默认使用模拟模式
      mode: config.mode || 'mock', // mock | homeassistant | mqtt | http | tuya | xiaomi
      baseUrl: config.baseUrl || 'http://localhost:8123',
      apiToken: config.apiToken || '',
      mqttBroker: config.mqttBroker || 'mqtt://localhost:1883',
      timeout: config.timeout || 3000, // 3秒超时保证快速响应
      cache: config.cache || true,
      cacheTimeout: config.cacheTimeout || 5000 // 5秒缓存
    };

    this.deviceCache = new Map();
    this.initializeAdapter();
  }

  initializeAdapter() {
    switch (this.config.mode) {
      case 'homeassistant':
        this.adapter = new HomeAssistantAdapter(this.config);
        break;
      case 'mqtt':
        this.adapter = new MQTTAdapter(this.config);
        break;
      case 'tuya':
        this.adapter = new TuyaAdapter(this.config);
        break;
      case 'xiaomi':
        this.adapter = new XiaomiAdapter(this.config);
        break;
      case 'http':
        this.adapter = new HTTPAdapter(this.config);
        break;
      default:
        this.adapter = new MockAdapter(this.config);
    }
  }

  /**
   * 统一的设备控制接口
   * @param {string} deviceId - 设备ID
   * @param {string} action - 动作: on/off/set/toggle
   * @param {object} params - 参数
   * @returns {Promise<object>} - 执行结果
   */
  async controlDevice(deviceId, action, params = {}) {
    const startTime = Date.now();

    try {
      // 检查缓存
      if (this.config.cache && action === 'get') {
        const cached = this.getCachedState(deviceId);
        if (cached) return cached;
      }

      // 调用适配器
      const result = await Promise.race([
        this.adapter.control(deviceId, action, params),
        this.timeout(this.config.timeout)
      ]);

      // 更新缓存
      if (this.config.cache) {
        this.updateCache(deviceId, result);
      }

      // 记录性能
      result.responseTime = Date.now() - startTime;

      return result;
    } catch (error) {
      console.error(`Device control failed: ${error.message}`);
      return {
        success: false,
        error: error.message,
        deviceId,
        responseTime: Date.now() - startTime
      };
    }
  }

  /**
   * 批量控制设备（并发执行）
   */
  async batchControl(commands) {
    const promises = commands.map(cmd =>
      this.controlDevice(cmd.deviceId, cmd.action, cmd.params)
    );
    return await Promise.allSettled(promises);
  }

  /**
   * 获取设备状态
   */
  async getDeviceStatus(deviceId) {
    return await this.controlDevice(deviceId, 'get', {});
  }

  /**
   * 获取所有设备状态（并发）
   */
  async getAllDevicesStatus(deviceIds) {
    const promises = deviceIds.map(id => this.getDeviceStatus(id));
    return await Promise.allSettled(promises);
  }

  // 缓存管理
  getCachedState(deviceId) {
    const cached = this.deviceCache.get(deviceId);
    if (cached && Date.now() - cached.timestamp < this.config.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  updateCache(deviceId, data) {
    this.deviceCache.set(deviceId, {
      data,
      timestamp: Date.now()
    });
  }

  timeout(ms) {
    return new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Operation timeout')), ms)
    );
  }
}

/**
 * Mock适配器 - 用于测试和开发
 */
class MockAdapter {
  constructor(config) {
    this.config = config;
    this.mockDevices = {
      'light_living_room': {
        type: 'light',
        name: '客厅灯',
        state: 'off',
        brightness: 100,
        color: '#ffffff'
      },
      'light_bedroom': {
        type: 'light',
        name: '卧室灯',
        state: 'off',
        brightness: 50,
        color: '#fff5dc'
      },
      'speaker_living_room': {
        type: 'speaker',
        name: '客厅音箱',
        state: 'off',
        volume: 50,
        playing: null
      },
      'tv_living_room': {
        type: 'tv',
        name: '客厅电视',
        state: 'off',
        channel: 1,
        volume: 30
      },
      'air_conditioner_living_room': {
        type: 'air_conditioner',
        name: '客厅空调',
        state: 'off',
        temperature: 25,
        mode: 'cool'
      },
      'curtain_bedroom': {
        type: 'curtain',
        name: '卧室窗帘',
        state: 'open',
        position: 100
      }
    };
  }

  async control(deviceId, action, params) {
    // 模拟网络延迟 (50-200ms)
    await new Promise(r => setTimeout(r, 50 + Math.random() * 150));

    const device = this.mockDevices[deviceId];
    if (!device) {
      throw new Error(`Device ${deviceId} not found`);
    }

    const oldState = { ...device };

    switch (action) {
      case 'on':
        device.state = 'on';
        break;
      case 'off':
        device.state = 'off';
        break;
      case 'toggle':
        device.state = device.state === 'on' ? 'off' : 'on';
        break;
      case 'set':
        Object.assign(device, params);
        break;
      case 'get':
        return {
          success: true,
          deviceId,
          state: device
        };
    }

    return {
      success: true,
      deviceId,
      action,
      oldState: oldState.state,
      newState: device.state,
      state: device
    };
  }
}

/**
 * Home Assistant适配器
 */
class HomeAssistantAdapter {
  constructor(config) {
    this.config = config;
    this.axios = require('axios').create({
      baseURL: config.baseUrl,
      timeout: config.timeout,
      headers: {
        'Authorization': `Bearer ${config.apiToken}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async control(deviceId, action, params) {
    const domain = deviceId.split('.')[0];
    const service = this.mapActionToService(domain, action);

    const response = await this.axios.post(
      `/api/services/${domain}/${service}`,
      {
        entity_id: deviceId,
        ...params
      }
    );

    return {
      success: true,
      deviceId,
      action,
      state: response.data
    };
  }

  mapActionToService(domain, action) {
    const mapping = {
      light: { on: 'turn_on', off: 'turn_off', toggle: 'toggle' },
      switch: { on: 'turn_on', off: 'turn_off', toggle: 'toggle' },
      media_player: { on: 'turn_on', off: 'turn_off', play: 'media_play', pause: 'media_pause' },
      climate: { on: 'turn_on', off: 'turn_off', set: 'set_temperature' },
      cover: { open: 'open_cover', close: 'close_cover', stop: 'stop_cover' }
    };

    return mapping[domain]?.[action] || action;
  }
}

/**
 * MQTT适配器
 */
class MQTTAdapter {
  constructor(config) {
    this.config = config;
    this.mqtt = require('mqtt');
    this.client = this.mqtt.connect(config.mqttBroker);
    this.setupSubscriptions();
  }

  setupSubscriptions() {
    this.client.on('connect', () => {
      this.client.subscribe('hoorii/devices/+/state');
    });
  }

  async control(deviceId, action, params) {
    return new Promise((resolve, reject) => {
      const topic = `hoorii/devices/${deviceId}/command`;
      const payload = JSON.stringify({ action, params });

      const timeout = setTimeout(() => {
        reject(new Error('MQTT command timeout'));
      }, this.config.timeout);

      // 订阅响应
      const responseTopic = `hoorii/devices/${deviceId}/response`;
      this.client.subscribe(responseTopic);

      this.client.once('message', (topic, message) => {
        if (topic === responseTopic) {
          clearTimeout(timeout);
          this.client.unsubscribe(responseTopic);
          resolve(JSON.parse(message.toString()));
        }
      });

      // 发送命令
      this.client.publish(topic, payload);
    });
  }
}

/**
 * HTTP通用适配器
 */
class HTTPAdapter {
  constructor(config) {
    this.config = config;
    this.axios = require('axios').create({
      baseURL: config.baseUrl,
      timeout: config.timeout,
      headers: {
        'Authorization': config.apiToken,
        'Content-Type': 'application/json'
      }
    });
  }

  async control(deviceId, action, params) {
    const response = await this.axios.post('/control', {
      deviceId,
      action,
      params
    });

    return response.data;
  }
}

/**
 * 涂鸦智能适配器（预留）
 */
class TuyaAdapter {
  constructor(config) {
    this.config = config;
    // TODO: 实现涂鸦API集成
  }

  async control(deviceId, action, params) {
    // 预留接口
    return {
      success: false,
      error: 'Tuya adapter not implemented yet'
    };
  }
}

/**
 * 小米米家适配器（预留）
 */
class XiaomiAdapter {
  constructor(config) {
    this.config = config;
    // TODO: 实现米家API集成
  }

  async control(deviceId, action, params) {
    // 预留接口
    return {
      success: false,
      error: 'Xiaomi adapter not implemented yet'
    };
  }
}

// n8n节点导出
module.exports = SmartHomeAdapter;

// 使用示例
if (require.main === module) {
  (async () => {
    // 创建适配器实例
    const adapter = new SmartHomeAdapter({
      mode: 'mock', // 使用模拟模式测试
      timeout: 2000,
      cache: true
    });

    // 单个设备控制
    console.log('Turning on living room light...');
    const result = await adapter.controlDevice('light_living_room', 'on', {
      brightness: 80,
      color: '#ffcc00'
    });
    console.log('Result:', result);

    // 批量控制
    console.log('\nBatch control...');
    const batchResults = await adapter.batchControl([
      { deviceId: 'light_bedroom', action: 'on' },
      { deviceId: 'speaker_living_room', action: 'on', params: { volume: 30 } },
      { deviceId: 'air_conditioner_living_room', action: 'set', params: { temperature: 23 } }
    ]);
    console.log('Batch results:', batchResults);

    // 获取所有设备状态
    console.log('\nGetting all device status...');
    const statuses = await adapter.getAllDevicesStatus([
      'light_living_room',
      'light_bedroom',
      'speaker_living_room'
    ]);
    statuses.forEach(s => console.log(s.value));
  })();
}