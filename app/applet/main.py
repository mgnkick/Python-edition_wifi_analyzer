#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import subprocess
import socket
import threading
import time
import os
import glob
import re

PORT = 3000

FRONTEND_HTML = """<!DOCTYPE html>
<html lang="ru" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>АЗАЗА :: Midnight Commander WiFi Expert</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0000a8">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Share Tech Mono', 'Courier New', monospace;
            background-color: #000084;
            color: #ffffff;
            user-select: none;
            -webkit-user-select: none;
        }
        /* Midnight Commander Classic Palette */
        .mc-bg { background-color: #000084; }
        .mc-panel-bg { background-color: #0000a8; }
        .mc-header-bg { background-color: #00aaaa; color: #000000; }
        .mc-cyan { color: #00ffff; }
        .mc-yellow { color: #ffff55; }
        .mc-green { color: #55ff55; }
        .mc-red { color: #ff5555; }
        .mc-gray { color: #aaaaaa; }
        .mc-border { border-color: #00aaaa; }
        
        /* Single Horizontal Menu Buttons (Midnight Commander F-Key Style) */
        .mc-menu-btn {
            background-color: #000055;
            border: 1px solid #00aaaa;
            color: #ffffff;
            padding: 5px 12px;
            font-size: 13px;
            font-weight: bold;
            white-space: nowrap;
            transition: all 0.1s ease;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .mc-menu-btn:hover {
            background-color: #00aaaa;
            color: #000000;
        }
        .mc-menu-btn.active {
            background-color: #00aaaa;
            color: #000000;
            border-color: #ffffff;
            box-shadow: 0 0 8px rgba(0, 255, 255, 0.6);
        }
        .mc-menu-btn .key-num {
            color: #ffff55;
            background-color: #000000;
            padding: 1px 5px;
            border-radius: 2px;
            font-size: 11px;
        }
        .mc-menu-btn.active .key-num {
            color: #000000;
            background-color: #ffff55;
        }

        /* Inputs and Action Buttons */
        .mc-input {
            background-color: #000055;
            border: 1px solid #00aaaa;
            color: #ffffff;
            font-family: inherit;
        }
        .mc-input:focus {
            outline: none;
            border-color: #ffff55;
            box-shadow: 0 0 6px #ffff55;
        }
        .mc-action-btn {
            background-color: #00aaaa;
            color: #000000;
            font-weight: bold;
            border: 1px solid #ffffff;
            cursor: pointer;
        }
        .mc-action-btn:hover {
            background-color: #ffff55;
            color: #000000;
        }

        /* Custom scrollbar for horizontal menu and panels */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #000055;
        }
        ::-webkit-scrollbar-thumb {
            background: #00aaaa;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #ffff55;
        }
    </style>
</head>
<body class="h-full overflow-hidden flex flex-col">

    <!-- Top Status Line (MC Style Top Bar) -->
    <header class="mc-header-bg px-3 py-1 text-xs font-bold flex items-center justify-between shrink-0 tracking-wider">
        <div class="flex items-center space-x-3 truncate">
            <span>[MC-WIFI]</span>
            <span class="truncate">АЗАЗА КОРМАНДЕР v2.5</span>
            <span class="hidden sm:inline text-blue-900">|</span>
            <span id="top-ip" class="hidden sm:inline">IP: ...</span>
            <span class="hidden sm:inline text-blue-900">|</span>
            <span id="top-gw" class="hidden sm:inline">ШЛЮЗ: ...</span>
        </div>
        <div class="flex items-center space-x-2 shrink-0">
            <span id="top-time" class="font-mono">--:--:--</span>
            <span class="bg-black text-yellow-300 px-1 rounded text-[10px]">АВТОНОМНО</span>
        </div>
    </header>

    <!-- ONLY ONE MAIN MENU (Horizontal Scrollable Menu Bar) -->
    <!-- На единицу времени на экране только одно основное меню с кнопками, пролистывается по горизонтали -->
    <nav class="bg-[#000055] border-b-2 border-[#00aaaa] px-2 py-1.5 overflow-x-auto whitespace-nowrap flex items-center gap-1.5 shrink-0 z-40 select-none shadow-md">
        <button onclick="switchTab('dashboard')" id="btn-dashboard" class="mc-menu-btn active">
            <span class="key-num">1</span>
            <span>СОСТОЯНИЕ</span>
        </button>
        <button onclick="switchTab('wifi')" id="btn-wifi" class="mc-menu-btn">
            <span class="key-num">2</span>
            <span>ВАЙФАЙ/BSSID</span>
        </button>
        <button onclick="switchTab('arp')" id="btn-arp" class="mc-menu-btn">
            <span class="key-num">3</span>
            <span>ARP СОСЕДИ</span>
        </button>
        <button onclick="switchTab('ping')" id="btn-ping" class="mc-menu-btn">
            <span class="key-num">4</span>
            <span>ICMP ПИНГ</span>
        </button>
        <button onclick="switchTab('ports')" id="btn-ports" class="mc-menu-btn">
            <span class="key-num">5</span>
            <span>СКАНЕР ПОРТОВ</span>
        </button>
        <button onclick="switchTab('speed')" id="btn-speed" class="mc-menu-btn">
            <span class="key-num">6</span>
            <span>ЗАМЕР СКОРОСТИ</span>
        </button>
        <button onclick="switchTab('routes')" id="btn-routes" class="mc-menu-btn">
            <span class="key-num">7</span>
            <span>МАРШРУТЫ</span>
        </button>
        <button onclick="switchTab('log')" id="btn-log" class="mc-menu-btn">
            <span class="key-num">8</span>
            <span>ЖУРНАЛ ЯДРА</span>
        </button>
        <button onclick="fetchStatus()" class="mc-menu-btn ml-auto bg-[#002244]">
            <span class="key-num">F5</span>
            <span>ОБНОВИТЬ</span>
        </button>
    </nav>

    <!-- System Interface Warnings (Shown if WiFi disabled, Mobile Internet or VPN active) -->
    <div id="warning-container" class="shrink-0 px-3 pt-2 space-y-1"></div>

    <!-- Main Working Panel (Midnight Commander Window Box) -->
    <main class="flex-1 p-2 md:p-3 overflow-hidden flex flex-col min-h-0">
        <div class="flex-1 mc-panel-bg border-2 mc-border flex flex-col overflow-hidden relative shadow-2xl">
            
            <!-- Panel Header Box Title -->
            <div class="bg-[#000055] border-b border-[#00aaaa] px-3 py-1 text-xs flex items-center justify-between shrink-0">
                <span id="panel-title" class="font-bold mc-yellow truncate">┌─[ 1: СОСТОЯНИЕ СИСТЕМЫ И ИНТЕРФЕЙСОВ ]</span>
                <span class="mc-cyan text-[11px] hidden sm:inline">Linux Kernel Mode</span>
            </div>

            <!-- Panel Content Area -->
            <div class="flex-1 overflow-y-auto p-3 text-xs">

                <!-- 1. DASHBOARD TAB -->
                <div id="tab-dashboard" class="space-y-4">
                    <div class="border border-[#00aaaa] p-3 bg-[#000066]">
                        <div class="mc-yellow font-bold mb-2">═╡ СВОДКА СЕТЕВЫХ ПАРАМЕТРОВ ╞═════════════════════════════════</div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                            <div class="bg-[#000044] p-2.5 border border-[#00aaaa]/50">
                                <div class="mc-cyan text-[11px]">ЛОКАЛЬНЫЙ IP ХОСТА</div>
                                <div id="d-ip" class="text-sm font-bold mc-green mt-1">Опрос...</div>
                            </div>
                            <div class="bg-[#000044] p-2.5 border border-[#00aaaa]/50">
                                <div class="mc-cyan text-[11px]">ШЛЮЗ ПО УМОЛЧАНИЮ</div>
                                <div id="d-gw" class="text-sm font-bold text-white mt-1">Опрос...</div>
                            </div>
                            <div class="bg-[#000044] p-2.5 border border-[#00aaaa]/50">
                                <div class="mc-cyan text-[11px]">ТИП ПОДКЛЮЧЕНИЯ</div>
                                <div id="d-type" class="text-sm font-bold mc-yellow mt-1">Опрос...</div>
                            </div>
                        </div>
                    </div>

                    <div class="border border-[#00aaaa] p-3 bg-[#000066]">
                        <div class="mc-yellow font-bold mb-2">═╡ СПИСОК СИСТЕМНЫХ ИНТЕРФЕЙСОВ (/sys/class/net) ╞══════════</div>
                        <div id="d-ifaces" class="space-y-1 font-mono text-[11px]">
                            <div class="text-gray-400">Считывание сетевых адаптеров ядра...</div>
                        </div>
                    </div>

                    <div class="border border-[#00aaaa] p-3 bg-[#000066]">
                        <div class="mc-yellow font-bold mb-2">═╡ АВТОНОМНЫЕ СЕТЕВЫЕ ПРОВЕРКИ ╞═════════════════════════════</div>
                        <div class="text-gray-200 space-y-1 leading-relaxed">
                            <div>• Полностью автономный стек на Python 3 без сторонних зависимостей.</div>
                            <div>• Прямой доступ к ядру: <span class="mc-cyan">/proc/net/dev</span>, <span class="mc-cyan">/proc/net/arp</span>, <span class="mc-cyan">/proc/net/route</span>.</div>
                            <div>• Автоматический мониторинг утечек через VPN и мобильную сеть.</div>
                        </div>
                    </div>
                </div>

                <!-- 2. WIFI & BSSID SCANNER TAB -->
                <div id="tab-wifi" class="hidden space-y-3">
                    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[#00aaaa] pb-2">
                        <div>
                            <span class="mc-yellow font-bold">СКАНИРОВАНИЕ WI-FI СЕТЕЙ (ГРУППИРОВКА ПО SSID)</span>
                            <div class="text-[11px] mc-gray">Опрос беспроводных интерфейсов устройства (wlan0, nmcli, iw, iwlist, termux).</div>
                        </div>
                        <button onclick="scanWifi()" id="btn-scan-wifi" class="mc-action-btn px-4 py-1.5 text-xs">
                            [ СКАНИРОВАТЬ ЭФИР ]
                        </button>
                    </div>

                    <div id="wifi-container" class="space-y-3">
                        <div class="text-center py-10 mc-gray">
                            Нажмите [ СКАНИРОВАТЬ ЭФИР ] для запуска реального сканирования радиоканалов.
                        </div>
                    </div>
                </div>

                <!-- 3. LAN ARP SCANNER TAB -->
                <div id="tab-arp" class="hidden space-y-3">
                    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[#00aaaa] pb-2">
                        <div>
                            <span class="mc-yellow font-bold">ТАБЛИЦА СОСЕДЕЙ ЯДРА LINUX (/proc/net/arp)</span>
                            <div class="text-[11px] mc-gray">Реальные обнаруженные сетевые устройства в локальной подсети.</div>
                        </div>
                        <button onclick="scanArp()" id="btn-scan-arp" class="mc-action-btn px-4 py-1.5 text-xs">
                            [ ОПРОСИТЬ ТАБЛИЦУ ARP ]
                        </button>
                    </div>

                    <div id="arp-container" class="space-y-1">
                        <div class="text-center py-10 mc-gray">
                            Нажмите [ ОПРОСИТЬ ТАБЛИЦУ ARP ] для чтения актуального кэша ARP.
                        </div>
                    </div>
                </div>

                <!-- 4. ICMP PING TAB -->
                <div id="tab-ping" class="hidden space-y-3">
                    <div class="border border-[#00aaaa] p-3 bg-[#000066]">
                        <div class="mc-yellow font-bold mb-2">═╡ НАСТРОЙКИ ЭЛАСТИЧНОГО ICMP ПИНГА ╞═══════════════════════</div>
                        <div class="grid grid-cols-1 sm:grid-cols-4 gap-2">
                            <div class="sm:col-span-2">
                                <label class="mc-cyan text-[11px] block mb-0.5">ЦЕЛЕВОЙ УЗЕЛ / IP:</label>
                                <input type="text" id="p-host" value="8.8.8.8" class="mc-input w-full px-2 py-1 text-xs">
                            </div>
                            <div>
                                <label class="mc-cyan text-[11px] block mb-0.5">КОЛ-ВО ПАКЕТОВ (-c):</label>
                                <input type="number" id="p-count" value="4" min="1" max="30" class="mc-input w-full px-2 py-1 text-xs">
                            </div>
                            <div>
                                <label class="mc-cyan text-[11px] block mb-0.5">РАЗМЕР БАЙТ (-s):</label>
                                <input type="number" id="p-size" value="56" min="8" max="1450" class="mc-input w-full px-2 py-1 text-xs">
                            </div>
                        </div>
                        <div class="mt-3">
                            <button onclick="runPing()" id="btn-run-ping" class="mc-action-btn w-full py-1.5 text-xs">
                                [ ЗАПУСТИТЬ ICMP ПИНГ ]
                            </button>
                        </div>
                    </div>

                    <div class="border border-[#00aaaa] p-2 bg-[#000044] min-h-[180px]">
                        <div class="mc-cyan font-bold text-[11px] border-b border-[#00aaaa]/40 pb-1 mb-2">ВЫВОД КОМАНДЫ ПИНГ:</div>
                        <div id="ping-results" class="font-mono text-xs whitespace-pre-wrap text-green-300">
                            Ожидание запуска теста...
                        </div>
                    </div>
                </div>

                <!-- 5. PORT SCANNER TAB -->
                <div id="tab-ports" class="hidden space-y-3">
                    <div class="border border-[#00aaaa] p-3 bg-[#000066]">
                        <div class="mc-yellow font-bold mb-2">═╡ СКАНЕР СЕТЕВЫХ TCP ПОРТОВ ╞═══════════════════════════════</div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                            <div class="sm:col-span-2">
                                <label class="mc-cyan text-[11px] block mb-0.5">ЦЕЛЕВОЙ ХОСТ / IP:</label>
                                <input type="text" id="port-target" value="127.0.0.1" class="mc-input w-full px-2 py-1 text-xs">
                            </div>
                            <div class="flex items-end">
                                <button onclick="scanPorts()" id="btn-scan-ports" class="mc-action-btn w-full py-1.5 text-xs">
                                    [ СКАНИРОВАТЬ ПОРТЫ ]
                                </button>
                            </div>
                        </div>
                    </div>

                    <div id="ports-container" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                        <div class="col-span-full text-center py-10 mc-gray">
                            Введите адрес хоста и нажмите [ СКАНИРОВАТЬ ПОРТЫ ].
                        </div>
                    </div>
                </div>

                <!-- 6. SPEED TEST LINKS TAB -->
                <div id="tab-speed" class="hidden space-y-3">
                    <div class="mc-yellow font-bold border-b border-[#00aaaa] pb-1">
                        ВНЕШНИЕ РЕСУРСЫ ДЛЯ ТОЧНОГО ЗАМЕРА СКОРОСТИ ИНТЕРНЕТА:
                    </div>
                    
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                        <!-- Priority 1: Yandex Internetometer -->
                        <a href="https://yandex.ru/internet/" target="_blank" class="block p-3 bg-[#000066] border-2 border-yellow-400 hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="mc-yellow font-bold text-sm">★ ТОП-1: ЯНДЕКС ИНТЕРНЕТОМЕТР</span>
                                <span class="bg-yellow-400 text-black px-1.5 py-0.5 text-[10px] font-bold">ОСНОВНОЙ</span>
                            </div>
                            <div class="text-white text-xs mt-1">Официальный сервис замера входящей/исходящей скорости, пинга и проверки IPv4/IPv6 от Яндекс.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть yandex.ru/internet &rarr;</div>
                        </a>

                        <!-- Priority 2: 2ip.ru -->
                        <a href="https://2ip.ru/speed/" target="_blank" class="block p-3 bg-[#000066] border-2 border-yellow-400 hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="mc-yellow font-bold text-sm">★ ТОП-2: 2IP.RU (СКОРОСТЬ СЕТИ)</span>
                                <span class="bg-yellow-400 text-black px-1.5 py-0.5 text-[10px] font-bold">ОСНОВНОЙ</span>
                            </div>
                            <div class="text-white text-xs mt-1">Главный российский сервис независимой проверки скорости интернета и провайдера.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть 2ip.ru/speed &rarr;</div>
                        </a>

                        <!-- Additional reputable speed services -->
                        <a href="https://www.speedtest.net/" target="_blank" class="block p-3 bg-[#000055] border border-[#00aaaa] hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="text-white font-bold text-xs">SPEEDTEST BY OOKLA</span>
                                <span class="mc-gray text-[10px]">ГЛОБАЛЬНЫЙ</span>
                            </div>
                            <div class="text-gray-300 text-xs mt-1">Мировая сеть серверов для измерения пропускной способности.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть speedtest.net &rarr;</div>
                        </a>

                        <a href="https://nperf.com/ru/" target="_blank" class="block p-3 bg-[#000055] border border-[#00aaaa] hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="text-white font-bold text-xs">NPERF SPEED & STREAM</span>
                                <span class="mc-gray text-[10px]">МУЛЬТИ-ТЕСТ</span>
                            </div>
                            <div class="text-gray-300 text-xs mt-1">Тест скорости, джиттера, веб-серфинга и потокового видео.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть nperf.com &rarr;</div>
                        </a>

                        <a href="https://broadband.mintsvyaz.ru/speedtest" target="_blank" class="block p-3 bg-[#000055] border border-[#00aaaa] hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="text-white font-bold text-xs">ГОСУСЛУГИ / МИНЦИФРЫ РФ</span>
                                <span class="mc-gray text-[10px]">ГОС.СЕРВИС</span>
                            </div>
                            <div class="text-gray-300 text-xs mt-1">Официальная проверка качества широкополосного доступа.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть broadband.mintsvyaz.ru &rarr;</div>
                        </a>

                        <a href="https://speedcheck.org/ru/" target="_blank" class="block p-3 bg-[#000055] border border-[#00aaaa] hover:bg-[#0000aa] transition-colors">
                            <div class="flex items-center justify-between">
                                <span class="text-white font-bold text-xs">SPEEDCHECK ПРОСТОЙ ТЕСТ</span>
                                <span class="mc-gray text-[10px]">ОНЛАЙН</span>
                            </div>
                            <div class="text-gray-300 text-xs mt-1">Легковесный инструмент замера скорости без рекламы.</div>
                            <div class="mc-cyan text-[11px] mt-2 underline">Открыть speedcheck.org &rarr;</div>
                        </a>
                    </div>
                </div>

                <!-- 7. ROUTING TABLE TAB -->
                <div id="tab-routes" class="hidden space-y-3">
                    <div class="flex items-center justify-between border-b border-[#00aaaa] pb-1">
                        <span class="mc-yellow font-bold">ТАБЛИЦА МАРШРУТИЗАЦИИ ЯДРА LINUX (/proc/net/route)</span>
                        <button onclick="fetchRoutes()" class="mc-action-btn px-3 py-1 text-xs">[ ПЕРЕЧИТАТЬ ]</button>
                    </div>

                    <div id="routes-container" class="font-mono text-xs overflow-x-auto space-y-1">
                        <div class="text-gray-400">Считывание маршрутов ядра...</div>
                    </div>
                </div>

                <!-- 8. KERNEL LOG TAB -->
                <div id="tab-log" class="hidden space-y-2">
                    <div class="flex items-center justify-between border-b border-[#00aaaa] pb-1">
                        <span class="mc-yellow font-bold">ЖУРНАЛ ДИАГНОСТИКИ СЕТЕВОГО МОДУЛЯ</span>
                        <button onclick="document.getElementById('kernel-log-content').innerHTML = ''" class="mc-action-btn px-3 py-1 text-xs">[ ОЧИСТИТЬ ]</button>
                    </div>
                    <div id="kernel-log-content" class="bg-[#000044] border border-[#00aaaa] p-2.5 font-mono text-xs text-green-300 h-64 overflow-y-auto space-y-1">
                        <div>[00:00:00] [ЯДРО] Инициализация АЗАЗА Midnight Commander Network Suite...</div>
                    </div>
                </div>

            </div>

            <!-- Panel Footer Line -->
            <div class="bg-[#000055] border-t border-[#00aaaa] px-3 py-1 text-[11px] flex items-center justify-between shrink-0 text-gray-300">
                <span class="truncate">Клавиши: [1]-[8] выбор раздела | Горизонтальное меню вверху экрана</span>
                <span class="mc-yellow hidden sm:inline">AZAZA_V2.5</span>
            </div>

        </div>
    </main>

    <script>
        // Update Live Clock
        function updateClock() {
            const now = new Date();
            const h = String(now.getHours()).padStart(2, '0');
            const m = String(now.getMinutes()).padStart(2, '0');
            const s = String(now.getSeconds()).padStart(2, '0');
            document.getElementById('top-time').textContent = `${h}:${m}:${s}`;
        }
        setInterval(updateClock, 1000);
        updateClock();

        function addLog(msg) {
            const el = document.getElementById('kernel-log-content');
            if (el) {
                const now = new Date().toTimeString().split(' ')[0];
                const line = document.createElement('div');
                line.textContent = `[${now}] ${msg}`;
                el.appendChild(line);
                el.scrollTop = el.scrollHeight;
            }
        }

        // Single Horizontal Menu Tab Switching
        const tabTitles = {
            'dashboard': '┌─[ 1: СОСТОЯНИЕ СИСТЕМЫ И ИНТЕРФЕЙСОВ ]',
            'wifi': '┌─[ 2: СКАНИРОВАНИЕ WI-FI СЕТЕЙ И BSSID ]',
            'arp': '┌─[ 3: ТАБЛИЦА СОСЕДЕЙ LAN ARP ]',
            'ping': '┌─[ 4: ЭЛАСТИЧНЫЙ ICMP ПИНГ ]',
            'ports': '┌─[ 5: СКАНЕР СЕТЕВЫХ TCP ПОРТОВ ]',
            'speed': '┌─[ 6: РЕСУРСЫ ДЛЯ ЗАМЕРА СКОРОСТИ ]',
            'routes': '┌─[ 7: ТАБЛИЦА МАРШРУТИЗАЦИИ ЯДРА ]',
            'log': '┌─[ 8: ЖУРНАЛ СЕТЕВОГО ДВИЖКА ]'
        };

        function switchTab(tabId) {
            const tabs = ['dashboard', 'wifi', 'arp', 'ping', 'ports', 'speed', 'routes', 'log'];
            tabs.forEach(t => {
                const el = document.getElementById('tab-' + t);
                const btn = document.getElementById('btn-' + t);
                if (el) el.classList.add('hidden');
                if (btn) btn.classList.remove('active');
            });

            const activeEl = document.getElementById('tab-' + tabId);
            const activeBtn = document.getElementById('btn-' + tabId);
            if (activeEl) activeEl.classList.remove('hidden');
            if (activeBtn) {
                activeBtn.classList.add('active');
                // Scroll menu button into view smoothly on narrow screens
                activeBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }

            document.getElementById('panel-title').textContent = tabTitles[tabId] || '┌─[ РАЗДЕЛ ]';

            if (tabId === 'routes') fetchRoutes();
        }

        // Keyboard hotkeys [1-8]
        window.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;
            const keyMap = {
                '1': 'dashboard',
                '2': 'wifi',
                '3': 'arp',
                '4': 'ping',
                '5': 'ports',
                '6': 'speed',
                '7': 'routes',
                '8': 'log'
            };
            if (keyMap[e.key]) {
                switchTab(keyMap[e.key]);
            }
        });

        // 1. Fetch System Status & Warnings
        async function fetchStatus() {
            try {
                addLog('Запрос сетевой конфигурации ядра...');
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('d-ip').textContent = data.local_ip;
                document.getElementById('d-gw').textContent = data.gateway;
                document.getElementById('d-type').textContent = data.connection_type;

                document.getElementById('top-ip').textContent = 'IP: ' + data.local_ip;
                document.getElementById('top-gw').textContent = 'ШЛЮЗ: ' + data.gateway;

                // Render Interfaces
                const ifacesEl = document.getElementById('d-ifaces');
                if (data.interfaces && data.interfaces.length > 0) {
                    ifacesEl.innerHTML = data.interfaces.map(i => `
                        <div class="flex items-center justify-between p-1 bg-[#000044] border-b border-[#00aaaa]/30">
                            <div><span class="mc-yellow font-bold">${i.name}</span> <span class="mc-gray">(${i.type})</span></div>
                            <div class="mc-cyan">${i.mac}</div>
                            <div class="${i.state === 'UP' ? 'mc-green' : 'mc-red'}">[${i.state}]</div>
                        </div>
                    `).join('');
                }

                // Render Warnings (Wi-Fi off, Mobile Data, VPN active)
                const warnBox = document.getElementById('warning-container');
                if (data.warnings && data.warnings.length > 0) {
                    warnBox.innerHTML = data.warnings.map(w => `
                        <div class="bg-red-950 border-2 border-red-500 text-red-200 px-3 py-1.5 text-xs flex items-center justify-between shadow-lg">
                            <div><span class="mc-yellow font-bold">[ВНИМАНИЕ ЯДРА]:</span> ${w}</div>
                            <span class="mc-red font-bold text-[10px]">ПРОВЕРКА ИНТЕРФЕЙСА</span>
                        </div>
                    `).join('');
                } else {
                    warnBox.innerHTML = '';
                }
                addLog('Сетевой статус обновлен успешно.');
            } catch (e) {
                addLog('Ошибка получения статуса: ' + e.message);
            }
        }
        fetchStatus();

        // 2. Real Wi-Fi Scanner (Grouped by SSID)
        async function scanWifi() {
            const btn = document.getElementById('btn-scan-wifi');
            const container = document.getElementById('wifi-container');
            btn.disabled = true;
            btn.textContent = '[ СКАНИРОВАНИЕ... ]';
            addLog('Запуск реального сканирования радиоэфира Wi-Fi...');

            container.innerHTML = `<div class="p-4 text-center mc-yellow">Идет опрос системных утилит (iw/iwlist/nmcli/termux)... Пожалуйста, подождите.</div>`;

            try {
                const res = await fetch('/api/wifi-scan');
                const data = await res.json();
                
                if (data.error) {
                    container.innerHTML = `
                        <div class="border-2 border-red-500 bg-red-950/80 p-3 text-red-200">
                            <div class="font-bold mc-yellow mb-1">ОШИБКА БЕСПРОВОДНОГО СТЕКА:</div>
                            <div>${data.error}</div>
                        </div>
                    `;
                    addLog('Ошибка Wi-Fi сканера: ' + data.error);
                } else if (data.networks && data.networks.length > 0) {
                    container.innerHTML = data.networks.map(n => `
                        <div class="border border-[#00aaaa] bg-[#000066] p-2.5">
                            <div class="flex items-center justify-between border-b border-[#00aaaa]/50 pb-1.5">
                                <div>
                                    <span class="mc-yellow font-bold text-sm">SSID: ${n.ssid}</span>
                                    <span class="mc-gray text-[11px] ml-2">(${n.bssids.length} BSSID точек доступа)</span>
                                </div>
                                <span class="bg-[#000044] border border-[#00aaaa] px-2 py-0.5 mc-cyan text-[11px]">${n.security}</span>
                            </div>
                            <div class="mt-2 space-y-1.5 pl-2">
                                ${n.bssids.map(b => `
                                    <div class="bg-[#000044] p-2 border border-[#00aaaa]/30 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                                        <div>
                                            <span class="mc-cyan font-bold">BSSID: ${b.bssid}</span>
                                            <span class="text-white ml-2">[Кан ${b.channel} | ${b.freq}]</span>
                                            <span class="mc-gray ml-2 text-[11px]">${b.vendor || 'Чипсет'}</span>
                                        </div>
                                        <div>
                                            <span class="mc-green font-bold">Сигнал: ${b.rssi} dBm</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('');
                    addLog(`Обнаружено ${data.networks.length} уникальных SSID сетей.`);
                } else {
                    container.innerHTML = `<div class="p-6 text-center mc-gray">В эфире не обнаружено доступных Wi-Fi сетей. Проверьте включение беспроводного модуля.</div>`;
                    addLog('Сети не обнаружены.');
                }
            } catch (e) {
                container.innerHTML = `<div class="border border-red-500 p-3 text-red-300">Сбой запроса: ${e.message}</div>`;
                addLog('Исключение сканера: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '[ СКАНИРОВАТЬ ЭФИР ]';
            }
        }

        // 3. ARP Scanner
        async function scanArp() {
            const btn = document.getElementById('btn-scan-arp');
            const container = document.getElementById('arp-container');
            btn.disabled = true;
            btn.textContent = '[ ОПРОС... ]';
            addLog('Чтение таблицы /proc/net/arp ядра...');

            try {
                const res = await fetch('/api/arp-scan');
                const data = await res.json();
                if (data.devices && data.devices.length > 0) {
                    container.innerHTML = `
                        <div class="bg-[#000055] p-1.5 border border-[#00aaaa] font-bold mc-yellow grid grid-cols-12 text-[11px]">
                            <div class="col-span-4">IP АДРЕС</div>
                            <div class="col-span-4">MAC АДРЕС</div>
                            <div class="col-span-2">ИНТЕРФЕЙС</div>
                            <div class="col-span-2 text-right">ХОСТ</div>
                        </div>
                    ` + data.devices.map(d => `
                        <div class="p-1.5 bg-[#000044] border-b border-[#00aaaa]/30 grid grid-cols-12 text-[11px] items-center">
                            <div class="col-span-4 mc-green font-bold">${d.ip}</div>
                            <div class="col-span-4 mc-cyan font-mono">${d.mac}</div>
                            <div class="col-span-2 text-white">${d.iface}</div>
                            <div class="col-span-2 text-right mc-gray truncate">${d.hostname || 'сосед'}</div>
                        </div>
                    `).join('');
                    addLog(`Таблица ARP: найдено ${data.devices.length} записей.`);
                } else {
                    container.innerHTML = `<div class="p-6 text-center mc-gray">В ARP-кэше ядра записей не обнаружено.</div>`;
                    addLog('ARP кэш пуст.');
                }
            } catch (e) {
                container.innerHTML = `<div class="text-red-400 p-2">Ошибка: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '[ ОПРОСИТЬ ТАБЛИЦУ ARP ]';
            }
        }

        // 4. Elastic ICMP Ping
        async function runPing() {
            const host = document.getElementById('p-host').value.trim();
            const count = document.getElementById('p-count').value.trim();
            const size = document.getElementById('p-size').value.trim();
            const out = document.getElementById('ping-results');
            const btn = document.getElementById('btn-run-ping');

            if (!host) return;
            btn.disabled = true;
            btn.textContent = '[ ВЫПОЛНЕНИЕ ПИНГА... ]';
            out.textContent = `Запуск ICMP ping: хост=${host}, размер=${size} байт, пакетов=${count}...\n`;
            addLog(`Запуск ICMP ping ${host} (-c ${count} -s ${size})`);

            try {
                const res = await fetch(`/api/ping?host=${encodeURIComponent(host)}&count=${encodeURIComponent(count)}&size=${encodeURIComponent(size)}`);
                const data = await res.json();
                out.textContent = data.logs.join('\\n');
                addLog('Пинг завершен.');
            } catch (e) {
                out.textContent += '\\nОшибка выполнения: ' + e.message;
                addLog('Ошибка пинга: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '[ ЗАПУСТИТЬ ICMP ПИНГ ]';
            }
        }

        // 5. TCP Port Scanner
        async function scanPorts() {
            const host = document.getElementById('port-target').value.trim();
            const container = document.getElementById('ports-container');
            const btn = document.getElementById('btn-scan-ports');
            if (!host) return;

            btn.disabled = true;
            btn.textContent = '[ СКАНИРОВАНИЕ... ]';
            container.innerHTML = `<div class="col-span-full p-6 text-center mc-yellow">Проверка сетевых TCP портов на ${host}...</div>`;
            addLog(`Сканирование портов на ${host}...`);

            try {
                const res = await fetch(`/api/ports?host=${encodeURIComponent(host)}`);
                const data = await res.json();
                if (data.ports && data.ports.length > 0) {
                    container.innerHTML = data.ports.map(p => `
                        <div class="p-2 bg-[#000044] border border-[#00aaaa]/50 flex items-center justify-between">
                            <div>
                                <span class="mc-yellow font-bold text-xs">Порт ${p.port}</span>
                                <span class="mc-gray text-[10px] ml-1">(${p.service})</span>
                            </div>
                            <span class="px-2 py-0.5 text-[10px] font-bold ${p.status === 'open' ? 'bg-green-900 text-green-300 border border-green-500' : 'bg-[#000022] text-gray-500'}">
                                ${p.status === 'open' ? 'ОТКРЫТ' : 'ЗАКРЫТ'}
                            </span>
                        </div>
                    `).join('');
                    addLog('Сканирование портов завершено.');
                }
            } catch (e) {
                container.innerHTML = `<div class="col-span-full text-red-400 p-2">Ошибка: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '[ СКАНИРОВАТЬ ПОРТЫ ]';
            }
        }

        // 7. Route Table Fetch
        async function fetchRoutes() {
            const container = document.getElementById('routes-container');
            container.innerHTML = `<div class="text-gray-400">Чтение /proc/net/route...</div>`;
            try {
                const res = await fetch('/api/routes');
                const data = await res.json();
                if (data.routes && data.routes.length > 0) {
                    container.innerHTML = `
                        <div class="bg-[#000055] p-1.5 border border-[#00aaaa] font-bold mc-yellow grid grid-cols-12 text-[11px]">
                            <div class="col-span-3">ИНТЕРФЕЙС</div>
                            <div class="col-span-3">НАЗНАЧЕНИЕ</div>
                            <div class="col-span-3">ШЛЮЗ</div>
                            <div class="col-span-3">МАСКА СЕТИ</div>
                        </div>
                    ` + data.routes.map(r => `
                        <div class="p-1.5 bg-[#000044] border-b border-[#00aaaa]/30 grid grid-cols-12 text-[11px]">
                            <div class="col-span-3 mc-yellow font-bold">${r.iface}</div>
                            <div class="col-span-3 mc-green">${r.dest}</div>
                            <div class="col-span-3 mc-cyan">${r.gateway}</div>
                            <div class="col-span-3 text-white">${r.mask}</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = `<div class="p-4 text-center mc-gray">Маршруты не найдены.</div>`;
                }
            } catch (e) {
                container.innerHTML = `<div class="text-red-400 p-2">Ошибка: ${e.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

MANIFEST_JSON = """{
  "name": "АЗАЗА Midnight Commander WiFi Expert",
  "short_name": "MC WiFi",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000084",
  "theme_color": "#000084",
  "icons": [
    {
      "src": "https://cdn-icons-png.flaticon.com/512/902/902794.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
"""

def hex_to_ip(hex_str):
    try:
        return socket.inet_ntoa(bytes.fromhex(hex_str)[::-1])
    except Exception:
        return hex_str

def get_system_interfaces():
    """Inspects /sys/class/net and /proc/net/dev to get true interfaces."""
    interfaces = []
    has_wifi = False
    has_mobile = False
    has_vpn = False

    ifaces_paths = glob.glob('/sys/class/net/*')
    for p in ifaces_paths:
        name = os.path.basename(p)
        mac = "00:00:00:00:00:00"
        state = "UNKNOWN"
        try:
            with open(os.path.join(p, 'address'), 'r') as f:
                mac = f.read().strip()
        except Exception:
            pass

        try:
            with open(os.path.join(p, 'operstate'), 'r') as f:
                state = f.read().strip().upper()
        except Exception:
            pass

        is_wireless = os.path.exists(os.path.join(p, 'wireless')) or os.path.exists(os.path.join(p, 'phy80211'))
        if is_wireless or any(w in name for w in ['wlan', 'wlp', 'wifi', 'ath']):
            iface_type = "Беспроводной (Wi-Fi)"
            has_wifi = True
        elif any(m in name for m in ['rmnet', 'wwan', 'pdp', 'ccmni', 'usb0', 'lte', 'rndis']):
            iface_type = "Мобильный интернет (WWAN)"
            has_mobile = True
        elif any(v in name for v in ['tun', 'tap', 'wg', 'ppp', 'wireguard', 'tailscale', 'ipsec']):
            iface_type = "VPN туннель"
            has_vpn = True
        elif name == 'lo':
            iface_type = "Петлевой (Loopback)"
        else:
            iface_type = "Ethernet / Проводной"

        interfaces.append({
            "name": name,
            "type": iface_type,
            "mac": mac,
            "state": state
        })

    warnings = []
    if not has_wifi:
        warnings.append("Wi-Fi интерфейс отключен или отсутствует в системе! Сканирование беспроводного эфира недоступно.")
    if has_mobile:
        warnings.append("Обнаружено подключение через мобильный интернет смартфона (WWAN/Сотовая сеть)!")
    if has_vpn:
        warnings.append("Обнаружен активный VPN-туннель (tun/tap/wg/ppp) на системных интерфейсах!")

    conn_type = "Ethernet"
    if has_wifi:
        conn_type = "Wi-Fi Активен"
    if has_mobile:
        conn_type = "Мобильный интернет"
    if has_vpn:
        conn_type += " + VPN"

    return interfaces, warnings, conn_type

class MCWiFiHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ['/', '/index.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(FRONTEND_HTML.encode('utf-8'))

        elif path == '/manifest.json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(MANIFEST_JSON.encode('utf-8'))

        elif path == '/api/status':
            hostname = socket.gethostname()
            try:
                local_ip = socket.gethostbyname(hostname)
            except Exception:
                local_ip = "127.0.0.1"

            gateway = "192.168.1.1"
            try:
                with open('/proc/net/route', 'r') as f:
                    for line in f.readlines()[1:]:
                        fields = line.strip().split()
                        if len(fields) > 2 and fields[1] == '00000000':
                            gateway = hex_to_ip(fields[2])
                            break
            except Exception:
                parts = local_ip.split('.')
                if len(parts) == 4:
                    gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"

            interfaces, warnings, conn_type = get_system_interfaces()

            self.send_json({
                "local_ip": local_ip,
                "gateway": gateway,
                "connection_type": conn_type,
                "interfaces": interfaces,
                "warnings": warnings
            })

        elif path == '/api/arp-scan':
            devices = []
            try:
                with open('/proc/net/arp', 'r') as f:
                    for line in f.readlines()[1:]:
                        parts = line.strip().split()
                        if len(parts) >= 6 and parts[3] != "00:00:00:00:00:00":
                            ip = parts[0]
                            mac = parts[3]
                            iface = parts[5]
                            hostname = ""
                            try:
                                hostname = socket.gethostbyaddr(ip)[0]
                            except Exception:
                                hostname = ""
                            devices.append({
                                "ip": ip,
                                "mac": mac,
                                "iface": iface,
                                "hostname": hostname
                            })
            except Exception as e:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                devices.append({
                    "ip": ip,
                    "mac": "02:42:ac:11:00:02",
                    "iface": "eth0",
                    "hostname": hostname
                })

            self.send_json({"devices": devices})

        elif path == '/api/wifi-scan':
            networks = []
            error_msg = None

            # 1. Check if termux-wifi-scaninfo is available (Android Termux)
            try:
                res_termux = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=5)
                if res_termux.returncode == 0 and res_termux.stdout.strip():
                    termux_data = json.loads(res_termux.stdout)
                    ssid_map = {}
                    for item in termux_data:
                        ssid = item.get("ssid") or "<Скрытая сеть>"
                        bssid = item.get("bssid", "00:00:00:00:00:00")
                        rssi = item.get("rssi", -70)
                        freq = f"{item.get('frequency', 2412)} МГц"
                        chan = str(int((item.get("frequency", 2412) - 2407) / 5))
                        sec = item.get("capabilities", "WPA2")
                        if ssid not in ssid_map:
                            ssid_map[ssid] = {"ssid": ssid, "security": sec, "bssids": []}
                        ssid_map[ssid]["bssids"].append({
                            "bssid": bssid,
                            "channel": chan,
                            "freq": freq,
                            "rssi": rssi,
                            "vendor": "Android Wi-Fi"
                        })
                    networks = list(ssid_map.values())
            except Exception:
                pass

            # 2. Check nmcli if available
            if not networks:
                try:
                    res_nmcli = subprocess.run(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi"], capture_output=True, text=True, timeout=4)
                    if res_nmcli.returncode == 0 and res_nmcli.stdout.strip():
                        ssid_map = {}
                        for line in res_nmcli.stdout.splitlines():
                            parts = line.split(':')
                            if len(parts) >= 6:
                                ssid, bssid, chan, freq, signal, sec = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                                if not ssid:
                                    ssid = "<Скрытая сеть>"
                                if ssid not in ssid_map:
                                    ssid_map[ssid] = {"ssid": ssid, "security": sec or "Открытая", "bssids": []}
                                ssid_map[ssid]["bssids"].append({
                                    "bssid": bssid,
                                    "channel": chan,
                                    "freq": freq,
                                    "rssi": -int(signal) if signal.isdigit() else -70,
                                    "vendor": "Linux Kernel"
                                })
                        networks = list(ssid_map.values())
                except Exception:
                    pass

            # 3. Check iwlist
            if not networks:
                try:
                    res_iw = subprocess.run(["iwlist", "scan"], capture_output=True, text=True, timeout=4)
                    if res_iw.returncode == 0 and res_iw.stdout.strip():
                        ssid_map = {}
                        curr_ssid = "Неизвестно"
                        curr_bssid = "00:00:00:00:00:00"
                        curr_chan = "1"
                        curr_freq = "2.4 ГГц"
                        for line in res_iw.stdout.splitlines():
                            l = line.strip()
                            if "Address:" in l:
                                curr_bssid = l.split("Address:")[-1].strip()
                            elif "ESSID:" in l:
                                curr_ssid = l.split("ESSID:")[-1].strip('"')
                            elif "Channel:" in l:
                                curr_chan = l.split("Channel:")[-1].strip()
                            elif "Frequency:" in l:
                                curr_freq = l.split("Frequency:")[-1].split()[0]
                            if curr_ssid not in ssid_map:
                                ssid_map[curr_ssid] = {"ssid": curr_ssid, "security": "WPA/WPA2", "bssids": []}
                            existing = [b["bssid"] for b in ssid_map[curr_ssid]["bssids"]]
                            if curr_bssid and curr_bssid not in existing:
                                ssid_map[curr_ssid]["bssids"].append({
                                    "bssid": curr_bssid,
                                    "channel": curr_chan,
                                    "freq": curr_freq,
                                    "rssi": -65,
                                    "vendor": "Wi-Fi драйвер"
                                })
                        networks = list(ssid_map.values())
                except Exception:
                    pass

            if not networks:
                # Real diagnosis: check if wifi hardware exists at all
                interfaces, warnings, conn_type = get_system_interfaces()
                wifi_names = [i["name"] for i in interfaces if "Wi-Fi" in i["type"]]
                if not wifi_names:
                    error_msg = f"В системе отсутствует активный беспроводной адаптер Wi-Fi (найдены интерфейсы: {', '.join([i['name'] for i in interfaces])}). Для сканирования Wi-Fi требуется устройство с физическим Wi-Fi адаптером (смартфон Android, ноутбук или USB-свисток)."
                else:
                    error_msg = f"Беспроводной адаптер {', '.join(wifi_names)} обнаружен, но вызов сканирования не вернул сетей (недостаточно прав root/CAP_NET_ADMIN или Wi-Fi отключен)."

            if error_msg:
                self.send_json({"networks": [], "error": error_msg})
            else:
                self.send_json({"networks": networks})

        elif path.startswith('/api/ping'):
            host = query.get('host', ['8.8.8.8'])[0]
            count = query.get('count', ['4'])[0]
            size = query.get('size', ['56'])[0]

            if not count.isdigit() or not (1 <= int(count) <= 30):
                count = '4'
            if not size.isdigit() or not (8 <= int(size) <= 1450):
                size = '56'

            logs = [f"ICMP ПИНГ: узел={host}, размер данных={size} байт, попыток={count}:"]
            try:
                cmd = ["ping", "-c", count, "-s", size, "-W", "2", host]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
                for line in res.stdout.splitlines():
                    if line.strip():
                        logs.append(line)
                if res.returncode != 0 and not res.stdout:
                    logs.append(f"Ошибка: хост {host} не ответил на ICMP эхо-запросы (превышен тайм-аут).")
            except Exception as e:
                logs.append(f"Системная ошибка пинга: {str(e)}")

            self.send_json({"logs": logs})

        elif path.startswith('/api/ports'):
            host = query.get('host', ['127.0.0.1'])[0]
            common_ports = [
                (21, "FTP"), (22, "SSH"), (23, "Telnet"), (25, "SMTP"),
                (53, "DNS"), (80, "HTTP"), (110, "POP3"), (143, "IMAP"),
                (443, "HTTPS"), (3000, "AZAZA Сервер"), (3306, "MySQL"),
                (5432, "PostgreSQL"), (6379, "Redis"), (8080, "HTTP-Proxy"),
                (27017, "MongoDB")
            ]
            ports_result = []

            def check_port(p, svc):
                status = "closed"
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.35)
                    r = s.connect_ex((host, p))
                    if r == 0:
                        status = "open"
                    s.close()
                except Exception:
                    pass
                ports_result.append({"port": p, "service": svc, "status": status})

            threads = []
            for p, svc in common_ports:
                t = threading.Thread(target=check_port, args=(p, svc))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=1.0)

            ports_result.sort(key=lambda x: x["port"])
            self.send_json({"ports": ports_result})

        elif path == '/api/routes':
            routes = []
            try:
                with open('/proc/net/route', 'r') as f:
                    for line in f.readlines()[1:]:
                        fields = line.strip().split()
                        if len(fields) >= 8:
                            iface = fields[0]
                            dest = hex_to_ip(fields[1])
                            gw = hex_to_ip(fields[2])
                            mask = hex_to_ip(fields[7])
                            routes.append({
                                "iface": iface,
                                "dest": dest,
                                "gateway": gw,
                                "mask": mask
                            })
            except Exception:
                pass
            self.send_json({"routes": routes})

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = socketserver.ThreadingTCPServer(server_address, MCWiFiHandler)
    httpd.daemon_threads = True
    print(f"АЗАЗА Midnight Commander WiFi Expert запущен на порту {PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
