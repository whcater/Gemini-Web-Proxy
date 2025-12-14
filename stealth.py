"""
在页面初始化时注入的JavaScript，用于隐藏自动化特征
"""

STEALTH_JS = """
// 隐藏 webdriver 属性
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 隐藏 Chrome 自动化扩展
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// 隐藏 Permissions 查询
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// 移除自动化相关的属性
delete navigator.__proto__.webdriver;

// 隐藏 Chrome 属性
Object.defineProperty(window, 'chrome', {
    get: () => {
        return {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    }
});

console.log('Stealth mode activated');
"""