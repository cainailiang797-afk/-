<template>
	<view class="app-container">
		<!-- 头部 -->
		<view class="header">
			<text class="header-title">欢迎使用</text>
			<text class="header-subtitle">找到车了么</text>
		</view>
		
		<!-- 标签切换 -->
		<view class="tab-container">
			<view 
				class="tab-item" 
				:class="{ active: currentTab === 0 }" 
				@tap="switchTab(0)"
			>
				<text class="tab-text">登录</text>
			</view>
			<view 
				class="tab-item" 
				:class="{ active: currentTab === 1 }" 
				@tap="switchTab(1)"
			>
				<text class="tab-text">注册</text>
			</view>
		</view>
		
		<!-- 登录表单 -->
		<view class="form-container" v-if="currentTab === 0">
			<view class="input-group">
				<input 
					class="form-input" 
					v-model="loginForm.username" 
					placeholder="请输入用户名"
				/>
			</view>
			<view class="input-group">
				<input 
					class="form-input" 
					password 
					v-model="loginForm.password" 
					placeholder="请输入密码"
				/>
			</view>
			<view class="submit-btn" @tap="handleLogin">
				<text class="submit-text">登录</text>
			</view>
		</view>
		
		<!-- 注册表单 -->
		<view class="form-container" v-if="currentTab === 1">
			<view class="input-group">
				<input 
					class="form-input" 
					v-model="registerForm.username" 
					placeholder="请输入用户名"
				/>
			</view>
			<view class="input-group">
				<input 
					class="form-input" 
					password 
					v-model="registerForm.password" 
					placeholder="请输入密码"
				/>
			</view>
			<view class="input-group">
				<input 
					class="form-input" 
					password 
					v-model="registerForm.confirmPassword" 
					placeholder="请再次输入密码"
				/>
			</view>
			<view class="submit-btn" @tap="handleRegister">
				<text class="submit-text">注册</text>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				currentTab: 0,
				loginForm: {
					username: '',
					password: ''
				},
				registerForm: {
					username: '',
					password: '',
					confirmPassword: ''
				}
			}
		},
		methods: {
			switchTab(index) {
				this.currentTab = index;
			},
			handleLogin() {
				if (!this.loginForm.username) {
					uni.showToast({
						title: '请输入用户名',
						icon: 'none'
					});
					return;
				}
				if (!this.loginForm.password) {
					uni.showToast({
						title: '请输入密码',
						icon: 'none'
					});
					return;
				}
				
				// 模拟登录请求
				const res = {
					code: 200,
					msg: '登录成功',
					data: {
						accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
						refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
						username: this.loginForm.username
					}
				};
				
				console.log('登录成功:', res);
				
				if (res.code == 200) {
					uni.showToast({
						title: '登录成功',
						icon: 'success'
					});
					
					// 存储登录状态和token
					uni.setStorageSync('isLoggedIn', true);
					uni.setStorageSync('username', this.loginForm.username);
					uni.setStorageSync('accessToken', res.data.accessToken);
					uni.setStorageSync('refreshToken', res.data.refreshToken);
					
					setTimeout(() => {
						uni.reLaunch({
							url: '/pages/index/index'
						});
					}, 1500);
					
				} else {
					uni.showToast({
						title: res.msg,
						icon: 'none'
					});
				}

			},
			handleRegister() {
				if (!this.registerForm.username) {
					uni.showToast({
						title: '请输入用户名',
						icon: 'none'
					});
					return;
				}
				if (!this.registerForm.password) {
					uni.showToast({
						title: '请输入密码',
						icon: 'none'
					});
					return;
				}
				if (!this.registerForm.confirmPassword) {
					uni.showToast({
						title: '请再次输入密码',
						icon: 'none'
					});
					return;
				}
				if (this.registerForm.password !== this.registerForm.confirmPassword) {
					uni.showToast({
						title: '两次密码输入不一致',
						icon: 'none'
					});
					return;
				}
				
				// 模拟注册请求
				const res = {
					code: 200,
					msg: '注册成功',
					data: {
						accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
						refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
						username: this.registerForm.username
					}
				};
				
				console.log('注册成功:', res);
				
				if (res.code == 200) {
					uni.showToast({
						title: '注册成功',
						icon: 'success'
					});
					
					// 存储登录状态和token
					uni.setStorageSync('isLoggedIn', true);
					uni.setStorageSync('username', this.registerForm.username);
					uni.setStorageSync('accessToken', res.data.accessToken);
					uni.setStorageSync('refreshToken', res.data.refreshToken);
					
					setTimeout(() => {
						uni.reLaunch({
							url: '/pages/index/index'
						});
					}, 1500);
					
				} else {
					uni.showToast({
						title: res.msg,
						icon: 'none'
					});
				}

			}
		}
	}
</script>

<style>
	.app-container {
		background-color: #ffffff;
		min-height: 100vh;
		padding: 0 60rpx;
	}

	.header {
		padding-top: 120rpx;
		padding-bottom: 60rpx;
		text-align: center;
	}

	.header-title {
		display: block;
		font-size: 48rpx;
		font-weight: bold;
		color: #333;
	}

	.header-subtitle {
		display: block;
		font-size: 28rpx;
		color: #0f88eb;
		margin-top: 16rpx;
	}

	.tab-container {
		display: flex;
		margin-bottom: 60rpx;
		border-bottom: 2rpx solid #e0e0e0;
	}

	.tab-item {
		flex: 1;
		text-align: center;
		padding: 24rpx 0;
		border-bottom: 4rpx solid transparent;
	}

	.tab-item.active {
		border-bottom-color: #0f88eb;
	}

	.tab-text {
		font-size: 32rpx;
		color: #666;
	}

	.tab-item.active .tab-text {
		color: #0f88eb;
		font-weight: bold;
	}

	.form-container {
		display: flex;
		flex-direction: column;
	}

	.input-group {
		margin-bottom: 40rpx;
	}

	.form-input {
		height: 88rpx;
		background-color: #f5f5f5;
		border-radius: 44rpx;
		padding: 0 40rpx;
		font-size: 28rpx;
	}

	.submit-btn {
		height: 88rpx;
		background-color: #0f88eb;
		border-radius: 44rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 40rpx;
	}

	.submit-text {
		font-size: 32rpx;
		font-weight: bold;
		color: #ffffff;
	}
</style>
