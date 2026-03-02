export default {
	data() {
		return {
			//设置默认的分享参数
			//如果页面不设置share，就触发这个默认的分享
			share: {
				title: '找到车了么',//自定义标题
				path: `/pages/index/index`,  //默认跳转首页
				imageUrl: "",  //可设置默认分享图，不设置默认截取头部5:4
			}
		}
	},
    onShareAppMessage(res) { //发送给朋友
		let that = this
		// 动态获取当前页面栈
		// let pages = getCurrentPages(); //获取所有页面栈实例列表
		// let nowPage = pages[pages.length - 1]; //当前页页面实例
		// // let prevPage = pages[pages.length - 2]; //上一页页面实例
		// that.share.path = `/${nowPage.route}`
		// console.log("that.share:", that.share);
		
		let curPage = getCurrentPages();
		let route = curPage[curPage.length - 1].route; //获取当前页面的路由
		let params = curPage[curPage.length - 1].options; //获取当前页面参数，如果有则返回参数的对象，没有参数返回空对象{}
		let query = '';
		let keys = Object.keys(params); //获取对象的key 返回对象key的数组
		if (keys.length > 0) {
			query = keys.reduce((pre, cur) => {
				return pre + cur + '=' + params[cur] + '&';
			}, '?').slice(0, -1);
		}
		console.log("route + query:", route + query)
		that.share.path = route + query;
		this.share.imageUrl = getApp().globalData.shareImg;
		return {
			title: this.share.title,
			path: this.share.imageUrl == true ? "pages/index/index?scene=" + getApp().globalData.uid : this.share.path,
			// imageUrl: this.share.imageUrl == true ? "https://market.ritaomeng.com/huodong/fenx2.png" : "",
			success(res) {
				console.log('success(res)==', res);
				uni.showToast({
					title: '分享成功',
					icon: 'none'
				})
			},
			fail(res) {
				console.log('fail(res)==', res);
				uni.showToast({
					title: '分享失败',
					icon: 'none'
				})
			}
		}
	},
	onShareTimeline(res) { //分享到朋友圈
	let that = this
		// 动态获取当前页面栈
		// let pages = getCurrentPages(); //获取所有页面栈实例列表
		// let nowPage = pages[pages.length - 1]; //当前页页面实例
		// // let prevPage = pages[pages.length - 2]; //上一页页面实例
		// that.share.path = `/${nowPage.route}`
		
		let curPage = getCurrentPages();
		let route = curPage[curPage.length - 1].route; //获取当前页面的路由
		let params = curPage[curPage.length - 1].options; //获取当前页面参数，如果有则返回参数的对象，没有参数返回空对象{}
		let query = '';
		let keys = Object.keys(params); //获取对象的key 返回对象key的数组
		if (keys.length > 0) {
			query = keys.reduce((pre, cur) => {
				return pre + cur + '=' + params[cur] + '&';
			}, '?').slice(0, -1);
		}
		console.log(route + query)
		that.share.path = route + query;
		
		return {
			title: this.share.title,
			path: this.share.path,
			imageUrl: this.share.imageUrl,
			success(res) {
				console.log('success(res)==', res);
				uni.showToast({
					title: '分享成功',
					icon: 'none'
				})
			},
			fail(res) {
				console.log('fail(res)==', res);
				uni.showToast({
					title: '分享失败',
					icon: 'none'
				})
			}
		}
	},
}