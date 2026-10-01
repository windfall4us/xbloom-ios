/* XB_IOS_P2A_V016 runtime: iOS-only request feedback, duplicate-write guard, network recovery. */
(function () {
  'use strict';
  function initP2A() {
    if (!document.documentElement.classList.contains('xb-ios-p0') ||
        !document.body.classList.contains('ios-app') ||
        !window.Capacitor || typeof api !== 'function') return;
    if (window.__xbP2AInstalled) return;
    window.__xbP2AInstalled = true;
    var previousApi = api;
    var active = new Set();
    var lastTap = null;
    var toastTimer = null;
    var toast = document.createElement('div');
    toast.id = 'xbP2AToast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    document.body.appendChild(toast);
    var banner = document.createElement('div');
    banner.id = 'xbP2ANetwork';
    banner.setAttribute('role', 'alert');
    banner.hidden = true;
    banner.innerHTML = '<span id="xbP2ANetworkText">无法连接服务器</span><button type="button" id="xbP2ARetry">检查连接</button>';
    document.body.appendChild(banner);
    function tell(message, kind) {
      toast.textContent = String(message).slice(0, 180);
      toast.dataset.kind = kind || 'info';
      toast.classList.add('visible');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { toast.classList.remove('visible'); }, 3200);
    }
    function networkError(e) {
      var msg = String(e && (e.message || e) || '');
      return e instanceof TypeError || (e && e.name === 'AbortError') ||
        /failed to fetch|network request failed|networkerror|load failed|internet connection|offline|timed out|timeout|connection refused|could not connect/i.test(msg);
    }
    function showNetwork(isWrite) {
      document.getElementById('xbP2ANetworkText').textContent = isWrite ?
        '连接异常：刚才的写入结果可能未知，请先核对数据，勿重复提交。' :
        '服务器连接异常，请检查 Wi-Fi 或服务器地址。';
      banner.hidden = false;
      if (isWrite) banner.dataset.uncertain = '1';
      tell(isWrite ? '请求结果未知，请检查记录后再操作' : '连接异常，可检查连接', 'error');
    }
    function markTap(button) {
      if (!button || button.disabled) return;
      lastTap = { button: button, at: Date.now() };
    }
    document.addEventListener('click', function (event) {
      var btn = event.target && event.target.closest && event.target.closest('button,input[type="submit"]');
      if (btn && btn.id !== 'xbP2ARetry') markTap(btn);
    }, true);
    function recognizedFeedback(url, result) {
      // Only report completed effects when response structure explicitly confirms them.
      var path = String(url).split('?')[0];
      if (path === '/api/beans' && result && result.bean && result.bean.bean_id) return '咖啡豆已创建';
      if (/\/adapt-dripper$/.test(path) && result && result.created === true) return '已生成滤杯适配候选';
      return '请求已返回，请核对页面结果';
    }
    api = async function xbP2AApi(url, opt) {
      var method = String(opt && opt.method || 'GET').toUpperCase();
      var write = !['GET', 'HEAD', 'OPTIONS'].includes(method);
      var key = method + ' ' + String(url);
      if (write && active.has(key)) {
        tell('正在提交，请勿重复点击', 'info');
        throw new Error('同一操作仍在提交中，已阻止重复请求');
      }
      var btn = null;
      var prevDisabled = false;
      if (write) {
        active.add(key);
        if (lastTap && Date.now() - lastTap.at < 1000) {
          btn = lastTap.button;
          lastTap = null;
          if (btn && btn.isConnected && !btn.disabled) {
            prevDisabled = btn.disabled;
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
            btn.classList.add('xb-p2a-busy');
          } else btn = null;
        }
      }
      try {
        var data = await previousApi(url, opt);
        if (banner.dataset.uncertain !== '1') banner.hidden = true;
        if (write) tell(recognizedFeedback(url, data), 'success');
        return data;
      } catch (e) {
        if (networkError(e)) showNetwork(write);
        else if (write) tell('请求未成功：' + String(e && e.message || e).slice(0, 80), 'error');
        throw e;
      } finally {
        if (write) active.delete(key);
        if (btn) {
          btn.disabled = prevDisabled;
          btn.removeAttribute('aria-busy');
          btn.classList.remove('xb-p2a-busy');
        }
      }
    };
    document.getElementById('xbP2ARetry').addEventListener('click', async function () {
      var retry = this;
      retry.disabled = true;
      try {
        // Explicitly read-only health probe: NEVER replay a POST/PATCH automatically.
        await previousApi('/api/health', { method: 'GET' });
        banner.hidden = true;
        delete banner.dataset.uncertain;
        tell('服务器连接已恢复，请先检查先前操作结果', 'success');
      } catch (e) {
        showNetwork(false);
      } finally {
        retry.disabled = false;
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initP2A, { once: true });
  else initP2A();
})();
