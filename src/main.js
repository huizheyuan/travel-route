// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import axios from 'axios'
import VueAxios from 'vue-axios'
import router from './router'
import $ from 'jquery'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.min.js';

import './assets/css/common.css';
import commonJs from './assets/js/common.js';
Vue.use(commonJs);

Vue.use(VueAxios, axios);
axios.defaults.withCredentials=true;
Vue.config.productionTip = false;

router.afterEach((to,from, next) => {
  window.scrollTo(0,0)
});

// 添加全局事件监控方法
Vue.prototype.resetSetItem = function (key, newVal) {
  if (key === 'watchStorage') {
    // 创建一个StorageEvent事件
    var newStorageEvent = document.createEvent('StorageEvent');
    const storage = {
      setItem: function (k, val) {
        sessionStorage.setItem(k, val);
        // 初始化创建的事件
        newStorageEvent.initStorageEvent('setItem', false, false, k, null, val, null, null);
        // 派发对象
        window.dispatchEvent(newStorageEvent)
      }
    }
    return storage.setItem(key, newVal);
  }
}


// 添加请求拦截器
axios.interceptors.request.use((config) => {
  // 在发送请求之前,格式化参数，增加token
  let data = config.data;
  let params = new URLSearchParams()
  for (var key in config.data) {
    params.append(key, data[key])
  }
  config.data = params;
  return config;
}, function (error) {
  return Promise.reject(error);
});
axios.interceptors.response.use(
  response => {
    return response;
  },error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 返回 401 清除token信息并跳转到登录页面
          store.commit(types.LOGOUT);
          router.replace({
            path: 'login',
            query: {redirect: router.currentRoute.fullPath}
          })
      }
    }
    return Promise.reject(error.response.data)
});



/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
