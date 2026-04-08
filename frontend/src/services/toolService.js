/**
 * 工具服务 - 与后端API交互获取工具信息
 */

import apiClient from './apiClient';

const toolService = {
  /**
   * 获取所有工具列表
   * @returns {Promise<Array>} 工具列表
   */
  async getTools() {
    try {
      const response = await apiClient.get('/tools');
      return response.data.tools || [];
    } catch (error) {
      console.error('获取工具列表失败:', error);
      return [];
    }
  },

  /**
   * 获取工具类别
   * @returns {Promise<Object>} 工具类别
   */
  async getToolCategories() {
    try {
      const response = await apiClient.get('/tools/categories');
      return response.data;
    } catch (error) {
      console.error('获取工具类别失败:', error);
      return {};
    }
  },

  /**
   * 获取工具版本信息
   * @returns {Promise<Object>} 工具版本信息
   */
  async getToolVersions() {
    try {
      const response = await apiClient.get('/tools/versions');
      return response.data;
    } catch (error) {
      console.error('获取工具版本信息失败:', error);
      return {};
    }
  },

  /**
   * 检查工具更新
   * @returns {Promise<Array>} 需要更新的工具列表
   */
  async checkToolUpdates() {
    try {
      const response = await apiClient.get('/tools/updates');
      return response.data;
    } catch (error) {
      console.error('检查工具更新失败:', error);
      return [];
    }
  },

  /**
   * 获取支持的扫描场景
   * @returns {Promise<Array>} 扫描场景列表
   */
  async getScanScenarios() {
    try {
      const response = await apiClient.get('/tools/scenarios');
      return response.data;
    } catch (error) {
      console.error('获取扫描场景失败:', error);
      return [];
    }
  },

  /**
   * 执行扫描场景
   * @param {string} scenarioName 场景名称
   * @param {Object} params 场景参数
   * @returns {Promise<Object>} 执行结果
   */
  async executeScanScenario(scenarioName, params) {
    try {
      const response = await apiClient.post('/tools/execute-scenario', {
        scenario_name: scenarioName,
        params
      });
      return response.data;
    } catch (error) {
      console.error('执行扫描场景失败:', error);
      throw error;
    }
  },

  /**
   * 并行执行多个工具
   * @param {Array} tasks 工具任务列表
   * @returns {Promise<Object>} 执行结果
   */
  async executeToolsInParallel(tasks) {
    try {
      const response = await apiClient.post('/tools/execute-parallel', {
        tasks
      });
      return response.data;
    } catch (error) {
      console.error('并行执行工具失败:', error);
      throw error;
    }
  }
};

export default toolService;
