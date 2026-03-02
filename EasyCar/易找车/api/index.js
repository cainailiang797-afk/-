// 通用网络请求封装
// const BASE_URL = 'http://192.168.1.52:8087/api'; // 后端服务基础地址
const BASE_URL = 'http://www.myeasycar.cn/api'; // 后端服务基础地址

/**
 * 刷新token
 * @returns {Promise} - 返回Promise对象
 */
async function refreshToken() {
  const refreshToken = uni.getStorageSync('refreshToken');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + '/refresh',
      method: 'POST',
      data: { refreshToken },
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.code === 200) {
          const { accessToken, refreshToken: newRefreshToken } = res.data.data;
          uni.setStorageSync('accessToken', accessToken);
          uni.setStorageSync('refreshToken', newRefreshToken);
          resolve(accessToken);
        } else {
          // 刷新失败，清除登录状态
          uni.removeStorageSync('isLoggedIn');
          uni.removeStorageSync('username');
          uni.removeStorageSync('accessToken');
          uni.removeStorageSync('refreshToken');
          reject(new Error('Token refresh failed'));
        }
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
}

/**
 * 通用请求方法
 * @param {string} url - 请求路径
 * @param {Object} options - 请求选项
 * @returns {Promise} - 返回Promise对象
 */
async function request(url, options = {}) {
  try {
    const accessToken = uni.getStorageSync('accessToken');
    
    const res = await new Promise((resolve, reject) => {
      uni.request({
        url: BASE_URL + url,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
          'Authorization': accessToken ? `Bearer ${accessToken}` : '',
          ...options.header
        },
        success: (res) => {
          resolve(res);
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
    
    if (res.statusCode === 200) {
      return res.data;
    } else if (res.statusCode === 401) {
      // Token过期，尝试刷新
      try {
        const newAccessToken = await refreshToken();
        // 重新发送请求
        return await new Promise((resolve, reject) => {
          uni.request({
            url: BASE_URL + url,
            method: options.method || 'GET',
            data: options.data || {},
            header: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${newAccessToken}`,
              ...options.header
            },
            success: (res) => {
              if (res.statusCode === 200) {
                resolve(res.data);
              } else {
                reject(new Error(`请求失败：${res.statusCode}`));
              }
            },
            fail: (err) => {
              reject(err);
            }
          });
        });
      } catch (error) {
        // 刷新失败，跳转到登录页
        uni.navigateTo({
          url: '/pages/login/index'
        });
        throw error;
      }
    } else {
      throw new Error(`请求失败：${res.statusCode}`);
    }
  } catch (error) {
    throw error;
  }
}

/**
 * POST请求方法
 * @param {string} url - 请求路径
 * @param {Object} data - 请求数据
 * @param {Object} options - 其他选项
 * @returns {Promise} - 返回Promise对象
 */
function post(url, data = {}, options = {}) {
  return request(url, {
    method: 'POST',
    data,
    ...options
  });
}

/**
 * 添加停车记录
 * @param {string} photo - 车辆照片
 * @param {string} parkingLocation - 车位号
 * @param {string} location - 停车位置（定位信息）
 * @returns {Promise} - 返回Promise对象
 */
export function addParking(photo, parkingLocation, location) {
  return post('/add', {
    photo,
	parkingLocation,
    location
  });
}

/**
 * 获取所有停车记录
 * @returns {Promise} - 返回Promise对象
 */
export function findAll() {
  return request('/list', {
    method: 'GET'
  });
}

/**
 * 登录
 * @param {string} username - 账号
 * @param {string} password - 密码
 */
export function login(username, password) {
  return post('/login', {
    username,
	password
  });
}

/**
 * 注册
 * @param {string} username - 账号
 * @param {string} password - 密码
 */
export function register(username, password) {
  return post('/register', {
    username,
	password
  });
}


// 导出其他可能需要的请求方法
export default {
  request,
  post,
  addParking,
  findAll,
  login
};
