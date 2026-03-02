<template>
	<view class="app-container">
<!-- 		<view class="header">
			<text class="header-title">个人中心</text>
		</view> -->
		
		<view class="content">
			<!-- 未登录状态 -->
			<view class="login-status" v-if="!isLoggedIn">
				<view class="avatar-placeholder">
					<text class="avatar-icon">👤</text>
				</view>
				<text class="login-text">请登录</text>
				<view class="login-btn" @tap="goLogin">
					<text class="login-btn-text">去登录</text>
				</view>
			</view>
			
			<!-- 已登录状态 -->
			<view class="login-status" v-else>
				<view class="avatar-placeholder">
					<text class="avatar-icon">👤</text>
				</view>
				<text class="username">{{username}}</text>
				<!-- <text class="login-time">登录时间：{{loginTime}}</text> -->
				<view class="logout-btn" @tap="logout">
					<text class="logout-btn-text">退出登录</text>
				</view>
			</view>
			
			<!-- 功能列表 -->
			<view class="function-list">
				<!-- <view class="function-item">
					<text class="function-icon">📞</text>
					<text class="function-text">联系客服</text>
					<text class="function-arrow">＞</text>
				</view> -->
				<view class="function-item">
					<text class="function-icon">ℹ️</text>
					<text class="function-text">关于我们</text>
					<text class="function-arrow">V1.0.0</text>
				</view>
				<view class="function-item">
					<text class="function-icon">⚙️</text>
					<text class="function-text">设置</text>
					<text class="function-arrow">＞</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				isLoggedIn: false,
				username: '',
				loginTime: ''
			}
		},
		onLoad() {
			this.checkLoginStatus();
		},
		onShow() {
			this.checkLoginStatus();
		},
		methods: {
			checkLoginStatus() {
				const isLoggedIn = uni.getStorageSync('isLoggedIn');
				const username = uni.getStorageSync('username');
				this.isLoggedIn = isLoggedIn || false;
				this.username = username || '';
				
				if (this.isLoggedIn) {
					const now = new Date();
					this.loginTime = now.toLocaleString();
				}
			},
			goLogin() {
				uni.navigateTo({
					url: '/pages/login/index'
				});
			},
			logout() {
				uni.showModal({
					title: '提示',
					content: '确定要退出登录吗？',
					confirmText: '确定',
					cancelText: '取消',
					success: (res) => {
						if (res.confirm) {
							uni.removeStorageSync('isLoggedIn');
							uni.removeStorageSync('username');
							uni.removeStorageSync('accessToken');
							uni.removeStorageSync('refreshToken');
							this.checkLoginStatus();
							uni.showToast({
								title: '已退出登录',
								icon: 'success'
							});
							setTimeout(() => {
								uni.switchTab({
									url: '/pages/index/index'
								});
							}, 1500);
						}
					}
				});
			}
		}
	}
</script>

<style>
	.app-container {
		background-color: #f5f5f5;
		min-height: 100vh;
	}

	.content {
		padding: 40rpx;
	}

	.login-status {
		background-color: white;
		border-radius: 16rpx;
		padding: 60rpx 40rpx;
		text-align: center;
		margin-bottom: 40rpx;
		box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.1);
	}

	.avatar-placeholder {
		width: 160rpx;
		height: 160rpx;
		border-radius: 80rpx;
		background-color: #f0f0f0;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 32rpx;
	}

	.avatar-icon {
		font-size: 80rpx;
	}

	.login-text {
		font-size: 32rpx;
		color: #666;
		margin-bottom: 32rpx;
	}

	.login-btn {
		width: 200rpx;
		height: 72rpx;
		background-color: #0f88eb;
		border-radius: 36rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 20rpx auto 0;
	}

	.login-btn-text {
		font-size: 28rpx;
		color: white;
		font-weight: bold;
	}

	.username {
		font-size: 36rpx;
		font-weight: bold;
		color: #333;
		margin-bottom: 16rpx;
	}

	.logout-btn {
		width: 200rpx;
		height: 72rpx;
		background-color: #ff4757;
		border-radius: 36rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 20rpx auto 0;
	}

	.logout-btn-text {
		font-size: 28rpx;
		color: white;
		font-weight: bold;
	}

	.function-list {
		background-color: white;
		border-radius: 16rpx;
		box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.1);
	}

	.function-item {
		display: flex;
		align-items: center;
		padding: 32rpx;
		border-bottom: 2rpx solid #f0f0f0;
	}

	.function-item:last-child {
		border-bottom: none;
	}

	.function-icon {
		font-size: 40rpx;
		margin-right: 32rpx;
		width: 40rpx;
		text-align: center;
	}

	.function-text {
		flex: 1;
		font-size: 32rpx;
		color: #333;
	}

	.function-arrow {
		font-size: 28rpx;
		color: #999;
	}
</style>
