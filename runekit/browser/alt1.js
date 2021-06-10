// https://github.com/skillbert/alt1/blob/master/alt1/base/alt1api.ts
// https://runeapps.org/apps/alt1/helpoutput.html

(function () {
    'use strict';

    // The RPC token is set to ensure that web content cannot call API directly
    // (even though if discovered, still cannot bypass profiles restriction)
    const RPC_TOKEN = '%%RPC_TOKEN%%'; // replaced in profile.py

    if (window.parent !== window) {
        // If running in subframe just use parent's alt1.
        // Can't run separate instances as we have request ids
        // that the native part don't know about
        let wnd = window;
        while(wnd.parent && wnd.parent !== wnd) {
            // this is not going to work cross origin
            wnd = wnd.parent;
        }

        window.alt1 = wnd.alt1;
        return;
    }

    // FIXME: Even though RPC is secure, this is not...
    let syncChan;
    let api;
    let channel = new Promise(function (resolve) {
        let setup = function(){
            new QWebChannel(qt.webChannelTransport, function (chan) {
                syncChan = chan;
                api = chan.objects.alt1;
                resolve(chan);
            });
        };
        if (typeof window.qt !== 'undefined') {
            setup();
        } else {
            document.addEventListener('DOMContentLoaded', setup);
        }
    });

    function str2ab(str) {
        let buf = new ArrayBuffer(str.length);
        let bufView = new Uint8ClampedArray(buf);
        for (let i=0, strLen=str.length; i < strLen; i++) {
            bufView[i] = str.charCodeAt(i) & 0xFF;
        }
        return bufView;
    }

    function syncRpc(msg, json) {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', 'rk:' + JSON.stringify(msg), false); // sync xhr
        xhr.overrideMimeType('text/plain; charset=x-user-defined');
        xhr.setRequestHeader('token', RPC_TOKEN);
        xhr.send(null);

        if (json) {
            return JSON.parse(xhr.responseText);
        }
        return xhr.responseText;
    }

    function asyncRpc(msg, responseType='') {
        return new Promise((resolve, reject) => {
            let xhr = new XMLHttpRequest();
            xhr.open('GET', 'rk:' + JSON.stringify(msg));
            xhr.setRequestHeader('token', RPC_TOKEN);
            xhr.responseType = responseType;
            xhr.addEventListener('load', (e) => {
                resolve(xhr.response);
            });
            xhr.addEventListener('error' ,(e) => {
                e.xhr = xhr;
                reject(e);
            });
            xhr.send();

            return xhr.response;
        })
    }

    function emit(param){
        let listeners = alt1.events[param.eventName];
        for(let i = 0; i < listeners.length; i++){
            try {
                listeners[i](param);
            }catch(e){
                console.error(e);
            }
        }
    }

    let lastGameActivity = window.performance.now();
    let drawCallId = 0;

    window.alt1 = {
        overlay: {},
        version: '1.2.0',
        versionint: 1002000,
        maxtransfer: 4000000, // also hardcoded in lib...
        skinName: '',
        captureMethod: '',
        permissionInstalled: true,
        permissionGameState: true,
        permissionOverlay: true,
        permissionPixel: true,
        lastWorldHop: 0,
        rsPing: 0,
        rsFps: 60,
        openInfo: '{}',
        events: {
            alt1pressed: [],
            menudetected: [],
            rslinked: [],
            rsunlinked: [],
            permissionchanged: [],
            daemonrun: [],
            userevent: [],
            rsfocus: [],
            rsblur: [],
        },

        get screenX() {
            if(!syncChan) return 0;
            return api.screenInfoX;
        },

        get screenY() {
            if(!syncChan) return 0;
            return api.screenInfoY;
        },

        get screenWidth() {
            if(!syncChan) return 0;
            return api.screenInfoWidth;
        },

        get screenHeight() {
            if(!syncChan) return 0;
            return api.screenInfoHeight;
        },

        get captureInterval() {
            if(!syncChan) return 1000;
            return api.captureInterval;
        },

        get mousePosition() {
            if(!syncChan) return 0;
            return api.mousePosition;
        },

        get rsLinked() {
            return !!api;
        },

        get rsX() {
            if(!syncChan) return 0;
            return api.gamePositionX;
        },

        get rsY() {
            if(!syncChan) return 0;
            return api.gamePositionY;
        },

        get rsWidth() {
            if(!syncChan) return 0;
            return api.gamePositionWidth;
        },

        get rsHeight() {
            if(!syncChan) return 0;
            return api.gamePositionHeight;
        },

        get rsScaling() {
            if(!syncChan) return 0;
            return api.gameScaling;
        },

        get rsActive() {
            if(!syncChan) return 0;
            return api.gameActive;
        },

        get rsLastActive() {
            return window.performance.now() - lastGameActivity;
        },

        get currentWorld() {
            if(!syncChan) return -1;
            return api.world || -1;
        },

        userResize(left, top, right, bottom) {
            window.resizeTo(right-left, bottom-top);
        },

        /**
         * Tells Alt1 to fetch identification information from the given url. The file should contain a json encoded object to be passed to the identifyApp function.
         */
        identifyAppUrl(url) {
            channel.then(function(chan){
                chan.objects.alt1.identifyAppUrl(url);
            });
        },

        openBrowser(url) {
            window.open(url, '_blank');
        },

        clearBinds() {
            window.alt1.clearTooltip();
        },

        // registerStatusDaemon(serverUrl, state) {
        // },
        // getStatusDaemonState() {
        //     return '';
        // },

        showNotification(title, message, icon) {
            // FIXME: Just use HTML5 Notification once QWebEngineNotification is implemented
            channel.then(function(chan){
                chan.objects.alt1.showNotification(title, message, icon);
            });
        },

        closeApp() {
            window.close();
        },

        setTooltip(tooltip) {
            channel.then(function(chan){
                chan.objects.alt1.setTooltip(tooltip);
            });
            return true;
        },

        clearTooltip() {
            this.setTooltip('');
        },

        setTaskbarProgress(type, progress) {
            channel.then(function(chan){
               chan.objects.alt1.setTaskbarProgress(type, progress);
            });
        },

        setTitleBarText(text) {

        },

        overLayRect(color, x, y, w, h, time, lineWidth) {
            channel.then(function(chan){
                chan.objects.alt1.overlayRect(drawCallId++, color, x, y, w, h, time, lineWidth);
            });
            return true;
        },
        overLayText(str, color, size, x, y, time) {
            return alt1.overLayTextEx(str, color, size, x, y, time, '', false, true);
        },
        overLayTextEx(str, color, size, x, y, time, fontname, centered, shadow) {
            channel.then(function(chan){
                chan.objects.alt1.overlayTextEx(drawCallId++, str, color, size, x, y, time, fontname, centered, shadow);
            });
            return true;
        },
        overLayLine(color, width, x1, y1, x2, y2, time) {
            channel.then(function(chan){
                chan.objects.alt1.overlayLine(drawCallId++, color, width, x1, y1, x2, y2, time);
            });
            return true;
        },
        overLayImage(x, y, imgstr, imgwidth, time) {
            channel.then(function(chan){
                chan.objects.alt1.overlayImage(drawCallId++, x, y, imgstr, imgwidth, time);
            });
            return true;
        },
        overLayClearGroup(group) {
            channel.then(function(chan){
                chan.objects.alt1.overlayClearGroup(drawCallId++, group);
            });
            return true;
        },
        overLaySetGroup(group) {
            channel.then(function(chan){
                chan.objects.alt1.overlaySetGroup(drawCallId++, group);
            });
            return true;
        },
        overLayFreezeGroup(group) {
            channel.then(function(chan){
                chan.objects.alt1.overlayFreezeGroup(drawCallId++, group);
            });
            return true;
        },
        overLayContinueGroup(group) {
            channel.then(function(chan){
                chan.objects.alt1.overlayContinueGroup(drawCallId++, group);
            });
            return true;
        },
        overLayRefreshGroup(group) {
            channel.then(function(chan){
                chan.objects.alt1.overlayRefreshGroup(drawCallId++, group);
            });
            return true;
        },
        overLaySetGroupZIndex(group, zIndex) {
            channel.then(function(chan){
                chan.objects.alt1.overlaySetGroupZIndex(drawCallId++, group, zIndex);
            });
            return true;
        },

        getRegion(x, y, w, h) {
            return syncRpc({func: 'getRegion', x: x, y: y, w: w, h: h});
        },
        // getRegionMulti(rectsjson) {
        //     return '';
        // },
        bindRegion(x, y, w, h) {
            return syncRpc({func: 'bindRegion', x: x, y: y, w: w, h: h}, true);
        },
        // bindScreenRegion(x, y, w, h) {
        //     return -1;
        // },
        bindGetRegion(id, x, y, w, h) {
            return syncRpc({func: 'bindGetRegion', id: id, x: x, y: y, w: w, h: h});
        },
        // bindReadString(id, fontname, x, y) {
        //     return '';
        // },
        // bindReadColorString(id, fontname, color, x, y) {
        //     return '';
        // },
        // // TODO: Used in AfkScape
        // bindReadStringEx(id, x, y, args) {
        //     return '';
        // },
        // bindReadRightClickString(id, x, y) {
        //     return '';
        // },
        // bindGetPixel(id, x, y) {
        //     return -1;
        // },
        // bindFindSubImg(id, imgstr, imgwidth, x, y, w, h) {
        //     return '';
        // },
        capture(x, y, w, h) {
            let data = syncRpc({func: 'getRegionRaw', x: x, y: y, w: w, h: h});
            return str2ab(data);
        },
        captureAsync(x, y, w, h) {
            return asyncRpc({func: 'getRegionRaw', x: x, y: y, w: w, h: h}, 'arraybuffer')
                .then((data) => new Uint8ClampedArray(data));
        },
        async captureMultiAsync(areas) {
            // XXX: This override the current bind
            let boundId = await asyncRpc({func: 'bindRegion', x: 0, y: 0, w: alt1.rsWidth, h: alt1.rsHeight}, 'json');
            let bounds = await Promise.all(Object.keys(areas).map((area) => {
                let value = areas[area];
                return asyncRpc({func: 'bindGetRegionRaw', id: boundId, x: value.x, y: value.y, w: value.width, h: value.height}, 'arraybuffer')
                    .then((data) => ({[area]: new Uint8ClampedArray(data)}));
            }));
            return bounds.reduce((a, b) => ({...a, ...b}), {});
        },
        bindGetRegionBuffer(id, x, y, w, h) {
            let data = syncRpc({func: 'bindGetRegionRaw', id: id, x: x, y: y, w: w, h: h});
            return str2ab(data);
        },
        addOCRFont(){
        },
    };

    channel.then(function(chan){
        let instance = chan.objects.alt1;
        instance.game_active_change_signal.connect(function(){
            let active = instance.gameActive;

            if(active){
                emit({eventName: 'rsfocus'});
            }else{
                emit({eventName: 'rsblur'});
            }
        });

        instance.game_activity_signal.connect(function(){
           lastGameActivity = window.performance.now();
        });

        instance.world_change_signal.connect(function(){
           alt1.lastWorldHop = new Date().getTime();
        });

        instance.alt1Signal.connect(function (pos){
            let mouseX = pos >> 16;
            let mouseY = pos & 0xFFFF;
            let event = {
                eventName: 'alt1pressed',
                text: '',
                mouseAbs: {
                    x: mouseX + instance.gamePositionX,
                    y: mouseY + instance.gamePositionY,
                },
                mouseRs: {
                    x: mouseX,
                    y: mouseY,
                },
                x: mouseX,
                y: mouseY,
                rsLinked: true,
            };
            emit(event);

            if (typeof window.alt1onrightclick !== 'undefined') {
                try{
                    window.alt1onrightclick(event);
                }catch(e){
                    console.error(e);
                }
            }
        })
    });

})();
