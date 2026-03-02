<template>
	<view class="app-container">
		
		<!-- 内容区域 -->
		<view class="content">
			<view v-if="loading" class="loading-container">
				<text class="loading-text">加载中...</text>
			</view>
			
			<view v-else-if="allParkingList.length === 0" class="empty-container">
				<text class="empty-text">暂无停车记录</text>
			</view>
			
			<view v-else class="list-container">
				<view 
					v-for="(item, index) in currentPageList" 
					:key="index" 
					class="parking-item-container"
				>
					<view class="parking-item">
						<view class="item-image" @tap.stop="previewImage(item.photo)">
							<image :src="item.photo" mode="aspectFill"></image>
							<view class="image-overlay">
								<text class="overlay-icon">👁️</text>
							</view>
						</view>
						<view class="item-content">
							<view class="item-header">
								<text class="item-location">{{item.location}}</text>
							</view>
							<view class="item-row">
								<text class="item-date">{{formatDate(item.createTime)}} {{formatTime(item.createTime)}}</text>
							</view>
						</view>
					</view>
					<view v-if="hasCoordinates(item)" class="item-map" @tap="openNavigation(item)">
						<map 
							:latitude="getItemLatitude(item)" 
							:longitude="getItemLongitude(item)" 
							:markers="getMarkers(item)" 
							:show-location="true"
							style="width: 100%; height: 100%;"
						></map>
						<view class="map-nav-overlay">
							<text class="map-nav-icon">🧭</text>
							<text class="map-nav-text">导航</text>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 分页控件 -->
			<view v-if="allParkingList.length > 0" class="pagination">
				<view class="page-btn" :class="{ disabled: currentPage === 1 }" @tap="prevPage">
					<text class="page-btn-text">上一页</text>
				</view>
				<view class="page-info">
					<text class="page-num">{{currentPage}}</text>
					<text class="page-total">/ {{totalPages}}</text>
				</view>
				<view class="page-btn" :class="{ disabled: currentPage === totalPages }" @tap="nextPage">
					<text class="page-btn-text">下一页</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { findAll } from '../../api/index.js';
	export default {
		data() {
			return {
				allParkingList: [],
				loading: true,
				currentPage: 1,
				pageSize: 10
			}
		},
		onLoad() {
			this.getParkingList();
		},
		computed: {
			totalPages() {
				return Math.ceil(this.allParkingList.length / this.pageSize);
			},
			currentPageList() {
				const start = (this.currentPage - 1) * this.pageSize;
				const end = start + this.pageSize;
				return this.allParkingList.slice(start, end);
			}
		},
		methods: {
			// 返回上一页
			goBack() {
				uni.navigateBack();
			},
			
			// 上一页
			prevPage() {
				if (this.currentPage > 1) {
					this.currentPage--;
				}
			},
			
			// 下一页
			nextPage() {
				if (this.currentPage < this.totalPages) {
					this.currentPage++;
				}
			},
			
			// 获取停车记录列表
			async getParkingList() {
				try {
					this.loading = true;
					const res = await findAll();
					console.log('获取停车记录成功:', res);
					
					// 按创建时间降序排序，最新的在前面
					this.allParkingList = res.data.sort((a, b) => {
						return new Date(b.createTime) - new Date(a.createTime);
					});
				} catch (error) {
					console.error('获取停车记录失败:', error);
					uni.showToast({
						title: '获取停车记录失败，请重试',
						icon: 'none'
					});
				} finally {
					this.loading = false;
				}
			},
			
			// 格式化日期
			formatDate(dateStr) {
				const date = new Date(dateStr);
				const year = date.getFullYear();
				const month = String(date.getMonth() + 1).padStart(2, '0');
				const day = String(date.getDate()).padStart(2, '0');
				return `${year}-${month}-${day}`;
			},
			
			// 格式化时间
			formatTime(dateStr) {
				const date = new Date(dateStr);
				const hours = String(date.getHours()).padStart(2, '0');
				const minutes = String(date.getMinutes()).padStart(2, '0');
				return `${hours}:${minutes}`;
			},
			
			// 判断是否是今天
			isToday(dateStr) {
				const today = new Date();
				const date = new Date(dateStr);
				return today.toDateString() === date.toDateString();
			},
			
			// 预览图片
			previewImage(imageUrl) {
				uni.previewImage({
					urls: [imageUrl],
					current: 0,
					success: function(res) {
						console.log('预览图片成功');
					},
					fail: function(err) {
						console.error('预览图片失败:', err);
					}
				});
			},
			
			// 判断是否有经纬度
			hasCoordinates(item) {
				if (item.location) {
					const lonMatch = item.location.match(/经度: ([\d.]+)/);
					const latMatch = item.location.match(/纬度: ([\d.]+)/);
					return !!(lonMatch && latMatch);
				}
				return false;
			},
			
			// 获取经纬度文本
			getCoordsText(item) {
				if (item.location) {
					const lonMatch = item.location.match(/经度: ([\d.]+)/);
					const latMatch = item.location.match(/纬度: ([\d.]+)/);
					if (lonMatch && latMatch) {
						return `经度: ${lonMatch[1]}  纬度: ${latMatch[1]}`;
					}
				}
				return '';
			},
			
			// 打开导航
			openNavigation(item) {
				const latitude = this.getItemLatitude(item);
				const longitude = this.getItemLongitude(item);
				
				uni.openLocation({
					latitude: latitude,
					longitude: longitude,
					name: '停车位置',
					address: item.location,
					scale: 18,
					success: function(res) {
						console.log('打开导航成功');
					},
					fail: function(err) {
						console.error('打开导航失败:', err);
						uni.showToast({
							title: '无法打开导航',
							icon: 'none'
						});
					}
				});
			},
			
			// 获取纬度
			getItemLatitude(item) {
				if (item.location) {
					const latMatch = item.location.match(/纬度: ([\d.]+)/);
					if (latMatch) {
						return parseFloat(latMatch[1]);
					}
				}
				return 39.9042;
			},
			
			// 获取经度
			getItemLongitude(item) {
				if (item.location) {
					const lonMatch = item.location.match(/经度: ([\d.]+)/);
					if (lonMatch) {
						return parseFloat(lonMatch[1]);
					}
				}
				return 116.4074;
			},
			
			// 获取地图标记
			getMarkers(item) {
				const latitude = this.getItemLatitude(item);
				const longitude = this.getItemLongitude(item);
				
				return [{
					id: 1,
					longitude,
					latitude,
					name: '停车位置',
					desc: item.location,
					// iconPath: '/static/logo.png',
					width: 30,
					height: 40
				}];
			},
			
			// 关闭地图
			closeMap() {
				this.expandedIndex = -1;
			}
		}
	}
</script>

<style>
	/* 全局样式 */
	.app-container {
		background-color: #f5f5f5;
		min-height: 100vh;
	}

	/* 顶部导航栏 */
	.nav-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 80rpx;
		background-color: white;
		padding: 0 20rpx;
		border-bottom: 1rpx solid #e0e0e0;
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.nav-left {
		flex: 1;
		display: flex;
		align-items: center;
	}

	.back-button {
		font-size: 36rpx;
		color: #333;
	}

	.nav-center {
		flex: 2;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.nav-title {
		font-size: 32rpx;
		font-weight: bold;
		color: #333;
	}

	.nav-right {
		flex: 1;
	}

	/* 内容区域 */
	.content {
		display: flex;
		flex-direction: column;
		min-height: calc(100vh - 80rpx);
	}

	/* 加载中状态 */
	.loading-container {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 300rpx;
	}

	.loading-text {
		font-size: 28rpx;
		color: #999;
	}

	/* 空状态 */
	.empty-container {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 300rpx;
	}

	.empty-text {
		font-size: 28rpx;
		color: #999;
	}

	/* 列表容器 */
	.list-container {
		padding: 20rpx 20rpx 0 20rpx;
	}

	/* 停车记录项 */
	.parking-item {
		display: flex;
		background-color: white;
		border-radius: 12rpx;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
		padding: 20rpx;
		margin-bottom: 20rpx;
	}

	/* 车辆照片 */
	.item-image {
		width: 250rpx;
		height: 250rpx;
		border-radius: 8rpx;
		overflow: hidden;
		margin-right: 20rpx;
		position: relative;
		cursor: pointer;
		flex-shrink: 0;
	}

	.item-map {
		width: 100%;
		height: 180rpx;
		border-radius: 0;
		overflow: hidden;
		position: relative;
	}

	.item-image image {
		width: 100%;
		height: 100%;
	}

	/* 图片预览覆盖层 */
	.image-overlay {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 40rpx;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.overlay-icon {
		font-size: 24rpx;
		color: white;
	}

	/* 点击效果 */
	.item-image:active {
		transform: scale(0.95);
		transition: transform 0.2s ease;
	}

	/* 记录内容 */
	.item-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}

	/* 记录头部 */
	.item-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12rpx;
	}

	.item-location {
		font-size: 28rpx;
		font-weight: 500;
		color: #333;
		flex: 1;
		margin-right: 12rpx;
	}

	.item-date {
		font-size: 24rpx;
		color: #999;
	}

	/* 记录底部 */
	.item-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.item-time {
		font-size: 24rpx;
		color: #999;
	}

	.item-status {
		font-size: 20rpx;
		padding: 4rpx 12rpx;
		border-radius: 12rpx;
		background-color: #f0f8ff;
		color: #0f88eb;
	}

	.item-status.old {
			background-color: #f5f5f5;
			color: #999;
		}

		/* 停车记录容器 */
		.parking-item-container {
			margin-bottom: 20rpx;
		}

		/* 地图容器 */
		.map-container {
			margin-top: 10rpx;
			background-color: white;
			border-radius: 12rpx;
			box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
			overflow: hidden;
		}

		.map-header {
			display: flex;
			align-items: center;
			justify-content: space-between;
			height: 60rpx;
			padding: 0 20rpx;
			border-bottom: 1rpx solid #e0e0e0;
		}

		.map-title {
			font-size: 28rpx;
			font-weight: 500;
			color: #333;
		}

		.map-close {
			font-size: 36rpx;
			color: #999;
			cursor: pointer;
		}

		.map-content {
			padding: 0;
		}

		/* 防止图片点击事件冒泡 */
		.item-image {
			pointer-events: auto;
		}
		
		/* 分页控件 */
		.pagination {
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 30rpx 0;
			gap: 40rpx;
		}
		
		.page-btn {
			padding: 16rpx 40rpx;
			background-color: #0f88eb;
			border-radius: 8rpx;
		}
		
		.page-btn.disabled {
			background-color: #e0e0e0;
		}
		
		.page-btn-text {
			font-size: 28rpx;
			color: white;
		}
		
		.page-btn.disabled .page-btn-text {
			color: #999;
		}
		
		.page-info {
			display: flex;
			align-items: baseline;
		}
		
		.page-num {
			font-size: 32rpx;
			font-weight: bold;
			color: #333;
		}
		
		.page-total {
			font-size: 24rpx;
			color: #999;
		}
</style>
