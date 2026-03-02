<template>
	<view class="app-container">
		
		<!-- 内容区域 -->
		<view class="content">
			<view class="card">
				<!-- 车位号输入 -->
				<view class="form-item">
					<text class="form-label">车位号</text>
					<view class="input-container">
						<input 
							class="form-input" 
							v-model="parkingLocation" 
							placeholder="请输入车位号，如：A区-123号"
						/>
					</view>
				</view>
				
				<!-- 照片上传 -->
				<view class="form-item">
					<text class="form-label">车辆照片（最多2张）</text>
					<view class="upload-container">
						<view class="upload-button" @tap="chooseImage" v-if="imageUrls.length < 2">
							<text class="upload-icon">+</text>
							<text class="upload-text">上传照片</text>
						</view>
						<view v-for="(url, index) in imageUrls" :key="index" class="image-preview">
							<image class="preview-image" :src="url" mode="aspectFill" @tap="previewImage(url)"></image>
							<text class="delete-image" @tap="deleteImage(index)">×</text>
						</view>
					</view>
				</view>
				
				<!-- 定位功能 -->
				<view class="form-item">
					<text class="form-label">停车位置</text>
					<view class="location-container">
						<view v-if="!location" class="location-button" @tap="getLocation">
							<text class="location-icon">📍</text>
							<text class="location-text">点击定位当前位置</text>
						</view>
						<view v-else class="location-info">
							<text class="location-icon">📍</text>
							<text class="location-detail">{{location}}</text>
							<text class="location-refresh" @tap="getLocation">↻</text>
						</view>
					</view>
					<view v-if="location" class="location-map">
						<map 
							:latitude="latitude" 
							:longitude="longitude" 
							:markers="getMarkers()" 
							:show-location="true"
							style="width: 100%; height: 200rpx;"
						></map>
					</view>
				</view>
				
				<!-- 提交按钮 -->
				<view class="submit-container">
					<view class="submit-button" @tap="submitForm">
						<text class="submit-text">提交</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { addParking } from '../../api/index.js';
	export default {
		data() {
			return {
				parkingLocation: '',
				imageUrls: [],
				location: '',
				latitude: null,
				longitude: null
			}
		},
		onLoad() {
			this.getLocation();
		},
		methods: {
			// 返回上一页
			goBack() {
				uni.navigateBack();
			},
			
			// 获取当前位置
			getLocation() {
				uni.showLoading({
					title: '定位中...'
				});
				
				uni.getLocation({
					type: 'gcj02',
					altitude: true,
					success: (res) => {
						console.log('定位成功:', res);
						this.latitude = res.latitude;
						this.longitude = res.longitude;
						this.location = `经度: ${res.longitude.toFixed(4)}, 纬度: ${res.latitude.toFixed(4)}`;
						uni.hideLoading();
					},
					fail: (err) => {
						console.error('定位失败:', err);
						uni.hideLoading();
						uni.showToast({
							title: '定位失败，请检查定位权限',
							icon: 'none'
						});
					}
				});
			},
			
			// 获取地图标记
			getMarkers() {
				if (this.latitude && this.longitude) {
					return [{
						id: 1,
						longitude: this.longitude,
						latitude: this.latitude,
						name: '停车位置',
						desc: this.location,
						width: 30,
						height: 40
					}];
				}
				return [];
			},
			
			// 选择图片
			chooseImage() {
				const remainingCount = 2 - this.imageUrls.length;
				if (remainingCount <= 0) {
					uni.showToast({
						title: '最多只能上传2张照片',
						icon: 'none'
					});
					return;
				}
				
				uni.chooseImage({
					count: remainingCount,
					sizeType: ['compressed'],
					sourceType: ['camera', 'album'],
					success: (res) => {
						res.tempFilePaths.forEach(path => {
							if (this.imageUrls.length < 2) {
								this.imageUrls.push(path);
							}
						});
					},
					fail: (err) => {
						console.error('选择图片失败:', err);
					}
				});
			},
			
			// 预览图片
			previewImage(url) {
				uni.previewImage({
					urls: this.imageUrls,
					current: url
				});
			},
			
			// 删除图片
			deleteImage(index) {
				this.imageUrls.splice(index, 1);
			},
			
			// 提交表单
			async submitForm() {
				// 表单验证
				// if (!this.parkingLocation) {
				// 	uni.showToast({
				// 		title: '请输入车位号',
				// 		icon: 'none'
				// 	});
				// 	return;
				// }
				
				if (this.imageUrls.length === 0) {
					uni.showToast({
						title: '请上传车辆照片',
						icon: 'none'
					});
					return;
				}
				
				try {
					// 这里应该先上传图片到服务器，获取图片URL
					// 模拟上传成功，使用临时路径作为图片URL
					const photoUrls = this.imageUrls.join(',');
					
					// 准备传递给后端的位置信息
					// 如果有定位信息，使用定位信息；否则使用车位号
					const locationInfo = this.location || this.parkingLocation;
					console.log('传递给后端的位置信息:', locationInfo);
					
					// 调用后端接口
					const res = await addParking(photoUrls, this.parkingLocation, this.location);
					console.log('停车记录添加成功:', res);
					
					// 显示成功提示
					uni.showToast({
						title: res.message || '停车成功',
						icon: 'success'
					});
					
					// 延迟返回上一页
					setTimeout(() => {
						this.goBack();
					}, 1500);
				} catch (error) {
					console.error('停车记录添加失败:', error);
					
					// 显示失败提示
					uni.showToast({
						title: '停车失败，请重试',
						icon: 'none'
					});
				}
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
		align-items: center;
		padding: 30rpx;
	}

	/* 卡片式设计 */
	.card {
		background-color: white;
		border-radius: 12rpx;
		box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
		padding: 30rpx;
		width: 100%;
		max-width: 600rpx;
	}

	/* 表单项 */
	.form-item {
		margin-bottom: 40rpx;
	}

	.form-label {
		display: block;
		font-size: 28rpx;
		font-weight: 500;
		color: #333;
		margin-bottom: 12rpx;
	}

	.input-container {
		border: 1rpx solid #e0e0e0;
		border-radius: 8rpx;
		padding: 0 20rpx;
	}

	.form-input {
		height: 80rpx;
		font-size: 28rpx;
		color: #333;
	}

	/* 定位相关样式 */
	.location-container {
		border: 1rpx solid #e0e0e0;
		border-radius: 8rpx;
		overflow: hidden;
	}

	.location-button {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 80rpx;
		background-color: #fafafa;
		cursor: pointer;
		transition: background-color 0.2s ease;
	}

	.location-button:active {
		background-color: #f0f0f0;
	}

	.location-icon {
		font-size: 32rpx;
		margin-right: 12rpx;
	}

	.location-text {
		font-size: 28rpx;
		color: #666;
	}

	.location-info {
		display: flex;
		align-items: center;
		padding: 0 20rpx;
		height: 80rpx;
		background-color: #f8f8f8;
	}

	.location-detail {
		flex: 1;
		font-size: 24rpx;
		color: #333;
		margin-right: 12rpx;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.location-refresh {
		font-size: 24rpx;
		color: #0f88eb;
		cursor: pointer;
		padding: 8rpx;
	}

	.location-refresh:active {
		transform: rotate(180deg);
		transition: transform 0.5s ease;
	}

	.location-map {
		margin-top: 15rpx;
		border-radius: 8rpx;
		overflow: hidden;
	}

	/* 上传区域 */
	.upload-container {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 20rpx;
	}

	.upload-button {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 2rpx dashed #e0e0e0;
		border-radius: 8rpx;
		width: 150rpx;
		height: 150rpx;
		background-color: #fafafa;
		cursor: pointer;
		flex-shrink: 0;
	}

	.upload-icon {
		font-size: 48rpx;
		color: #999;
		margin-bottom: 8rpx;
	}

	.upload-text {
		font-size: 20rpx;
		color: #999;
		text-align: center;
	}

	.image-preview {
		position: relative;
		width: 150rpx;
		height: 150rpx;
		border-radius: 8rpx;
		overflow: hidden;
		flex-shrink: 0;
	}

	.preview-image {
		width: 100%;
		height: 100%;
	}

	.delete-image {
		position: absolute;
		top: 6rpx;
		right: 6rpx;
		width: 32rpx;
		height: 32rpx;
		border-radius: 50%;
		background-color: rgba(0, 0, 0, 0.5);
		color: white;
		font-size: 24rpx;
		text-align: center;
		line-height: 32rpx;
		cursor: pointer;
	}

	/* 提交按钮 */
	.submit-container {
		margin-top: 60rpx;
	}

	.submit-button {
		height: 80rpx;
		background-color: #0f88eb;
		border-radius: 40rpx;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.submit-button:active {
		background-color: #0c73cc;
		transform: scale(0.98);
	}

	.submit-text {
		color: white;
		font-size: 32rpx;
		font-weight: bold;
	}
</style>
