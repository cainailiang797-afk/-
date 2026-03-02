<template>
	<view class="app-container">
		<!-- 头部 -->
		<view class="header">
			<view class="header-glow"></view>
			<text class="header-title">找到车了么</text>
			<text class="header-subtitle">智能停车 · 轻松找车</text>
		</view>
		
		<!-- 内容区域 -->
		<view class="content">
			<view class="buttons-container">
				<view class="button parking-button" @tap="parkCar">
					<view class="button-glow"></view>
					<view class="button-icon">🚗</view>
					<text class="button-text">停车</text>
					<view class="button-ring"></view>
				</view>
				<view class="button find-button" @tap="findCar">
					<view class="button-glow"></view>
					<view class="button-icon">🔍</view>
					<text class="button-text">找车</text>
					<view class="button-ring"></view>
				</view>
			</view>
		</view>
		
		<!-- 底部装饰 -->
		<view class="footer-decoration">
			<view class="decoration-line"></view>
			<text class="footer-text">让停车更简单</text>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				title: 'Hello'
			}
		},
		onLoad() {

		},
		methods: {
			checkLogin(callback) {
				const isLoggedIn = uni.getStorageSync('isLoggedIn');
				if (!isLoggedIn) {
					uni.showModal({
						title: '提示',
						content: '请先登录',
						confirmText: '去登录',
						success: (res) => {
							if (res.confirm) {
								uni.navigateTo({
									url: '/pages/login/index'
								});
							}
						}
					});
					return false;
				}
				return true;
			},
			parkCar() {
				console.log('停车按钮被点击');
				
				if (!this.checkLogin()) {
					return;
				}
				
				uni.navigateTo({
					url: '/pages/park/index'
				});
			},
			findCar() {
				console.log('找车按钮被点击');
				
				if (!this.checkLogin()) {
					return;
				}
				
				uni.navigateTo({
					url: '/pages/find/index'
				});
			}
		}
	}
</script>

<style>
	/* 全局样式 */
	.app-container {
		background: #ffffff;
		min-height: 100vh;
		position: relative;
		overflow: hidden;
	}

	/* 背景装饰 */
	.app-container::before {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: 
			radial-gradient(circle at 20% 80%, rgba(15, 136, 235, 0.08) 0%, transparent 50%),
			radial-gradient(circle at 80% 20%, rgba(0, 168, 107, 0.06) 0%, transparent 50%);
		animation: backgroundMove 20s ease-in-out infinite;
	}

	@keyframes backgroundMove {
		0%, 100% { transform: translate(0, 0) rotate(0deg); }
		50% { transform: translate(-2%, 2%) rotate(1deg); }
	}

	/* 头部样式 */
	.header {
		position: relative;
		padding: 180rpx 40rpx 40rpx;
		text-align: center;
		z-index: 2;
	}

	.header-glow {
		display: none;
	}

	.header-title {
		display: block;
		font-size: 60rpx;
		font-weight: 800;
		background: linear-gradient(135deg, #0f88eb 0%, #00a86b 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		text-shadow: 0 4rpx 20rpx rgba(15, 136, 235, 0.2);
		letter-spacing: 4rpx;
		position: relative;
	}

	.header-subtitle {
		display: block;
		font-size: 26rpx;
		color: #999;
		margin-top: 16rpx;
		letter-spacing: 6rpx;
		text-transform: uppercase;
	}

	/* 内容区域 */
	.content {
		position: relative;
		z-index: 2;
		padding: 60rpx 40rpx;
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	/* 按钮容器 */
	.buttons-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 80rpx;
	}

	/* 按钮样式 */
	.button {
		width: 320rpx;
		height: 320rpx;
		border-radius: 50%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		position: relative;
		overflow: visible;
		background: #0f88eb;
	}

	/* 按钮主体 */
	.button-bg {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		border-radius: 50%;
		background: #0f88eb;
	}

	/* 按钮图标 */
	.button-icon {
		font-size: 96rpx;
		margin-bottom: 24rpx;
		position: relative;
		z-index: 1;
	}

	/* 按钮文本 */
	.button-text {
		font-size: 52rpx;
		font-weight: 700;
		letter-spacing: 12rpx;
		position: relative;
		z-index: 1;
		color: #ffffff;
	}

	/* 底部装饰 */
	.footer-decoration {
		position: relative;
		z-index: 2;
		padding: 40rpx;
		text-align: center;
	}

	.decoration-line {
		width: 120rpx;
		height: 2rpx;
		background: #e0e0e0;
		margin: 0 auto 20rpx;
	}

	.footer-text {
		font-size: 22rpx;
		color: #999;
		letter-spacing: 4rpx;
	}
</style>
