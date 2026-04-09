/**
 * 服务配置
 * VITE_USE_MOCK_DATA 环境变量控制是否在API失败时使用模拟数据
 * 默认为 false，API失败时抛出真实错误
 */
export const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';
