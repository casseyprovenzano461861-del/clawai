/**
 * 工具管理组件 - 展示和管理安全工具
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, Button, Select, Input, Table, Badge, Alert } from '@/components/design-system';
import toolService from '../services/toolService';

const ToolManager = () => {
  const [activeTab, setActiveTab] = useState('tools');
  const [tools, setTools] = useState([]);
  const [categories, setCategories] = useState({});
  const [toolVersions, setToolVersions] = useState({});
  const [scanScenarios, setScanScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [scenarioParams, setScenarioParams] = useState({});
  const [executionResult, setExecutionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [outdatedTools, setOutdatedTools] = useState([]);

  // 加载工具和场景数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [toolsData, categoriesData, versionsData, scenariosData, updatesData] = await Promise.all([
        toolService.getTools(),
        toolService.getToolCategories(),
        toolService.getToolVersions(),
        toolService.getScanScenarios(),
        toolService.checkToolUpdates()
      ]);
      setTools(toolsData);
      setCategories(categoriesData);
      setToolVersions(versionsData);
      setScanScenarios(scenariosData);
      setOutdatedTools(updatesData);
    } catch (err) {
      setError('加载数据失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 处理场景参数变化
  const handleParamChange = (paramName, value) => {
    setScenarioParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // 执行扫描场景
  const handleExecuteScenario = async () => {
    if (!selectedScenario) {
      setError('请选择扫描场景');
      return;
    }

    setLoading(true);
    setError(null);
    setExecutionResult(null);

    try {
      const result = await toolService.executeScanScenario(selectedScenario, scenarioParams);
      setExecutionResult(result);
    } catch (err) {
      setError('执行扫描场景失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 处理场景选择变化
  const handleScenarioChange = (scenarioName) => {
    setSelectedScenario(scenarioName);
    setScenarioParams({});
    setExecutionResult(null);
  };

  // 获取场景参数
  const getScenarioParams = (scenarioName) => {
    const scenario = scanScenarios.find(s => s.name === scenarioName);
    return scenario ? scenario.params : [];
  };

  // 获取工具类别名称
  const getCategoryName = (category) => {
    return categories[category] || category;
  };

  // 获取工具状态
  const getToolStatus = (toolName) => {
    const versionInfo = toolVersions[toolName];
    if (!versionInfo) return '未知';
    if (!versionInfo.installed) return '未安装';
    if (versionInfo.update_info.is_outdated) return '需要更新';
    return '正常';
  };

  // 获取工具状态颜色
  const getStatusColor = (status) => {
    switch (status) {
      case '正常': return 'bg-green-100 text-green-800';
      case '需要更新': return 'bg-yellow-100 text-yellow-800';
      case '未安装': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* 错误提示 */}
      {error && (
        <Alert variant="destructive">
          {error}
        </Alert>
      )}

      {/* 工具更新提示 */}
      {outdatedTools.length > 0 && (
        <Alert variant="warning">
          有 {outdatedTools.length} 个工具需要更新
        </Alert>
      )}

      {/* 标签页导航 */}
      <div className="border-b border-gray-700 mb-4">
        <div className="flex space-x-4">
          <button
            onClick={() => setActiveTab('tools')}
            className={`px-4 py-2 ${activeTab === 'tools' ? 'border-b-2 border-blue-500 text-blue-500' : 'opacity-70'}`}
          >
            工具列表
          </button>
          <button
            onClick={() => setActiveTab('scenarios')}
            className={`px-4 py-2 ${activeTab === 'scenarios' ? 'border-b-2 border-blue-500 text-blue-500' : 'opacity-70'}`}
          >
            扫描场景
          </button>
          <button
            onClick={() => setActiveTab('versions')}
            className={`px-4 py-2 ${activeTab === 'versions' ? 'border-b-2 border-blue-500 text-blue-500' : 'opacity-70'}`}
          >
            版本管理
          </button>
        </div>
      </div>

      {/* 工具列表 */}
      {activeTab === 'tools' && (
        <div className="mt-4">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(categories).map(([category, name]) => {
                const categoryTools = tools.filter(tool => tool.category === category);
                if (categoryTools.length === 0) return null;
                
                return (
                  <Card key={category}>
                    <div className="p-4 border-b border-gray-700">
                      <h3 className="text-lg font-bold">{name}</h3>
                      <p className="text-sm opacity-70">共 {categoryTools.length} 个工具</p>
                    </div>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="min-w-full">
                          <thead>
                            <tr className="border-b border-gray-700">
                              <th className="px-4 py-2 text-left">工具名称</th>
                              <th className="px-4 py-2 text-left">描述</th>
                              <th className="px-4 py-2 text-left">状态</th>
                            </tr>
                          </thead>
                          <tbody>
                            {categoryTools.map(tool => (
                              <tr key={tool.name} className="border-b border-gray-700">
                                <td className="px-4 py-2 font-medium">{tool.name}</td>
                                <td className="px-4 py-2">{tool.description}</td>
                                <td className="px-4 py-2">
                                  <Badge className={getStatusColor(getToolStatus(tool.name))}>
                                    {getToolStatus(tool.name)}
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 扫描场景 */}
      {activeTab === 'scenarios' && (
        <div className="mt-4">
          <Card>
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-bold">扫描场景</h3>
              <p className="text-sm opacity-70">选择并执行预设的扫描场景</p>
            </div>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">选择场景</label>
                  <Select
                    value={selectedScenario}
                    onValueChange={handleScenarioChange}
                  >
                    <option value="">请选择扫描场景</option>
                    {scanScenarios.map(scenario => (
                      <option key={scenario.name} value={scenario.name}>
                        {scenario.name}
                      </option>
                    ))}
                  </Select>
                </div>

                {selectedScenario && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-2">场景参数</h3>
                      {getScenarioParams(selectedScenario).map(param => (
                        <div key={param.name} className="mb-2">
                          <label className="block text-xs font-medium mb-1">
                            {param.name} {param.required && <span className="text-red-500">*</span>}
                          </label>
                          <Input
                            type="text"
                            placeholder={param.description}
                            value={scenarioParams[param.name] || ''}
                            onChange={(e) => handleParamChange(param.name, e.target.value)}
                          />
                        </div>
                      ))}
                    </div>

                    <Button
                      onClick={handleExecuteScenario}
                      disabled={loading}
                      className="w-full"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          执行中...
                        </>
                      ) : (
                        '执行扫描'
                      )}
                    </Button>
                  </div>
                )}

                {executionResult && (
                  <div className="mt-4 p-4 border rounded">
                    <h3 className="text-sm font-medium mb-2">执行结果</h3>
                    <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-60">
                      {JSON.stringify(executionResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 版本管理 */}
      {activeTab === 'versions' && (
        <div className="mt-4">
          <Card>
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-bold">工具版本管理</h3>
              <p className="text-sm opacity-70">查看工具版本和更新状态</p>
            </div>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="px-4 py-2 text-left">工具名称</th>
                      <th className="px-4 py-2 text-left">当前版本</th>
                      <th className="px-4 py-2 text-left">最新版本</th>
                      <th className="px-4 py-2 text-left">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(toolVersions).map(([toolName, info]) => (
                      <tr key={toolName} className="border-b border-gray-700">
                        <td className="px-4 py-2 font-medium">{toolName}</td>
                        <td className="px-4 py-2">{info.version || '未安装'}</td>
                        <td className="px-4 py-2">{info.update_info.latest_version}</td>
                        <td className="px-4 py-2">
                          <Badge className={getStatusColor(getToolStatus(toolName))}>
                            {getToolStatus(toolName)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ToolManager;
