// https://github.com/skillbert/alt1/blob/master/alt1/base/alt1api.ts
// https://runeapps.org/apps/alt1/helpoutput.html

(function () {
    'use strict';

    // The RPC token is set to ensure that web content cannot call API directly
    // (even though if discovered, still cannot bypass profiles restriction)
    const RPC_TOKEN = '%%RPC_TOKEN%%'; // replaced in profile.py

    // FIXME: Even though RPC is secure, this is not...
    let syncChan;
    let channel = new Promise(function (resolve) {
        let setup = function(){
            new QWebChannel(qt.webChannelTransport, function (_channel) {
                syncChan = _channel;
                resolve(_channel);
            });
        };
        if (typeof window.qt !== 'undefined') {
            setup()
        } else {
            document.addEventListener('DOMContentLoaded', setup);
        }
    });

    function syncRpc(msg, json) {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', 'rk:' + JSON.stringify(msg), false); // sync xhr
        xhr.setRequestHeader('token', RPC_TOKEN);
        xhr.send(null);

        if (json) {
            return JSON.parse(xhr.responseText);
        }
        return xhr.responseText;
    }

    window.alt1 = {
        overlay: {},
        version: '1.1.1',
        versionint: 1001001,
        maxtransfer: 4000000, // also hardcoded in lib...
        skinName: '',
        captureMethod: '',
        permissionInstalled: true,
        permissionGameState: true,
        permissionOverlay: true,
        permissionPixel: true,
        rsX: 0,
        rsY: 0,
        rsWidth: 0,
        rsHeight: 0,
        rsScaling: 0,
        rsActive: true,
        rsLastActive: 0,
        lastWorldHop: 0,
        currentWorld: -1,
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
            return syncChan.objects.alt1.screenInfoX;
        },

        get screenY() {
            if(!syncChan) return 0;
            return syncChan.objects.alt1.screenInfoY;
        },

        get screenWidth() {
            if(!syncChan) return 0;
            return syncChan.objects.alt1.screenInfoWidth;
        },

        get screenHeight() {
            if(!syncChan) return 0;
            return syncChan.objects.alt1.screenInfoHeight;
        },

        get captureInterval() {
            if(!syncChan) return 1000;
            return syncChan.objects.alt1.captureInterval;
        },

        get mousePosition() {
            if(!syncChan) return 0;
            return syncChan.objects.alt1.mousePosition;
        },

        get rsLinked() {
            return !!syncChan;
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

        // openBrowser(url) {
        // },

        // clearBinds() {
        // },

        // registerStatusDaemon(serverUrl, state) {
        // },
        // getStatusDaemonState() {
        //     return '';
        // },

        // showNotification() {
        // },

        closeApp() {
            window.close()
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
            document.title = text;
        },

        // overLayRect(color, x, y, w, h, time, lineWidth) {
        //     return false;
        // },
        // overLayTextEx(str, color, size, x, y, time, fontname, centered, shadow) {
        //     return false;
        // },
        // overLayLine(color, width, x1, y1, x2, y2, time) {
        //     return false;
        // },
        // overLayImage(x, y, imgstr, imgwidth, time) {
        //     return false;
        // },
        // overLayClearGroup(group) {
        // },
        // overLaySetGroup(group) {
        // },
        // overLayFreezeGroup(group) {
        // },
        // overLayContinueGroup(group) {
        // },
        // overLayRefreshGroup(group) {
        // },
        // overLaySetGroupZIndex(groupname, zIndex) {
        // },

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
        // }
    };

    function updateGamePosition(){
        let pos = JSON.parse(syncChan.objects.alt1.gamePosition);
        alt1.rsX = pos.x;
        alt1.rsY = pos.y;
        alt1.rsWidth = pos.width;
        alt1.rsHeight = pos.height;
        alt1.rsScaling = pos.scaling;
    }

    channel.then(function(chan){
        chan.objects.alt1.update_game_position_signal.connect(updateGamePosition);
        updateGamePosition();
    });

})();
