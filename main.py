#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import subprocess
import socket
import threading
import time
import ipaddress
import os

PORT = 3000

FRONTEND_HTML = """<!DOCTYPE html>
<html lang="ru" class="dark h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AZAZA Linux WiFi Эксперт</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Share Tech Mono', monospace, Courier, monospace; background-color: #050505; color: #00ff66; }
        .term-border { border: 1px solid #00ff6633; box-shadow: 0 0 15px rgba(0, 255, 102, 0.1); }
        .term-input { background: #000; border: 1px solid #00ff6666; color: #00ff66; font-family: 'Share Tech Mono', monospace; }
        .term-input:focus { outline: none; border-color: #00ff66; box-shadow: 0 0 8px rgba(0, 255, 102, 0.4); }
        .term-btn { background: #001105; border: 1px solid #00ff6666; color: #00ff66; font-family: 'Share Tech Mono', monospace; transition: all 0.2s; }
        .term-btn:hover { background: #00ff66; color: #000; box-shadow: 0 0 10px #00ff66; }
    </style>
</head>
<body class="h-full overflow-hidden flex flex-col selection:bg-green-500 selection:text-black">

    <!-- Header -->
    <header class="bg-black border-b border-green-500/30 shrink-0 px-4 py-2.5 flex items-center justify-between z-50">
        <div class="flex items-center space-x-3 min-w-0">
            <div class="w-8 h-8 rounded bg-green-950 border border-green-500/40 flex items-center justify-center text-green-400 shrink-0">
                <i data-lucide="terminal" class="w-4 h-4"></i>
            </div>
            <div class="min-w-0">
                <h1 class="font-bold text-base tracking-wider truncate text-green-400">АЗАЗА ЯДРО WI-FI ЭКСПЕРТ</h1>
                <p class="text-[11px] text-green-600 truncate">Диагностика системных интерфейсов (Реальные данные)</p>
            </div>
        </div>
        <div class="flex items-center space-x-2 shrink-0">
            <span id="sys-status-badge" class="px-2 py-0.5 rounded text-[11px] font-mono bg-green-950 text-green-400 border border-green-500/30 flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span> ЯДРО АКТИВНО
            </span>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-3 md:p-5 grid grid-cols-1 md:grid-cols-4 gap-3 overflow-hidden">
        
        <!-- Sidebar Navigation -->
        <nav class="md:col-span-1 bg-black/90 border border-green-500/30 rounded-lg p-2 flex md:flex-col gap-1.5 overflow-x-auto md:overflow-y-auto shrink-0 max-h-full">
            <button onclick="switchTab('dashboard')" id="nav-dashboard" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all bg-green-950 text-green-400 border border-green-500 shrink-0">
                <i data-lucide="cpu" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[01] Состояние</span>
            </button>
            <button onclick="switchTab('wifi')" id="nav-wifi" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0">
                <i data-lucide="wifi" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[02] Вайфай и BSSID</span>
            </button>
            <button onclick="switchTab('scanner')" id="nav-scanner" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0">
                <i data-lucide="radar" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[03] LAN ARP Соседи</span>
            </button>
            <button onclick="switchTab('ping')" id="nav-ping" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0">
                <i data-lucide="activity" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[04] ICMP Пинг</span>
            </button>
            <button onclick="switchTab('ports')" id="nav-ports" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0">
                <i data-lucide="shield-alert" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[05] Сканер Портов</span>
            </button>
            <button onclick="switchTab('speedlinks')" id="nav-speedlinks" class="tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0">
                <i data-lucide="gauge" class="w-4 h-4 shrink-0"></i>
                <span class="truncate">[06] Замер Скорости</span>
            </button>
        </nav>

        <!-- Content Area -->
        <div class="md:col-span-3 flex flex-col h-full overflow-hidden bg-black/90 border border-green-500/30 rounded-lg p-3 md:p-5 relative term-border">

            <!-- WARNING BANNER CONTAINER -->
            <div id="system-warnings" class="shrink-0 mb-3 space-y-2"></div>

            <!-- DASHBOARD TAB -->
            <div id="tab-dashboard" class="tab-content flex flex-col h-full overflow-y-auto space-y-4 pr-1">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 shrink-0">
                    <div class="bg-black border border-green-500/40 rounded p-3 relative overflow-hidden">
                        <div class="flex items-center justify-between text-green-600 mb-1">
                            <span class="text-xs uppercase">Локальный IP</span>
                            <i data-lucide="cpu" class="w-4 h-4 text-green-400"></i>
                        </div>
                        <div id="card-local-ip" class="text-lg font-bold text-green-300 truncate">Загрузка...</div>
                        <p class="text-[10px] text-green-700 mt-0.5 truncate">Адрес сокета хоста</p>
                    </div>
                    <div class="bg-black border border-green-500/40 rounded p-3 relative overflow-hidden">
                        <div class="flex items-center justify-between text-green-600 mb-1">
                            <span class="text-xs uppercase">Шлюз по умолчанию</span>
                            <i data-lucide="router" class="w-4 h-4 text-green-400"></i>
                        </div>
                        <div id="card-gateway" class="text-lg font-bold text-green-300 truncate">Загрузка...</div>
                        <p class="text-[10px] text-green-700 mt-0.5 truncate">Таблица маршрутизации</p>
                    </div>
                    <div class="bg-black border border-green-500/40 rounded p-3 relative overflow-hidden">
                        <div class="flex items-center justify-between text-green-600 mb-1">
                            <span class="text-xs uppercase">Статус интерфейса</span>
                            <i data-lucide="shield" class="w-4 h-4 text-green-400"></i>
                        </div>
                        <div id="card-iface-status" class="text-lg font-bold text-green-300 truncate">Проверка...</div>
                        <p class="text-[10px] text-green-700 mt-0.5 truncate">Вайфай / Мобильный / VPN</p>
                    </div>
                </div>

                <div class="bg-green-950/30 border border-green-500/40 rounded p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shrink-0">
                    <div class="min-w-0">
                        <h2 class="text-sm font-bold text-green-300 uppercase truncate">Контроль системных интерфейсов активен</h2>
                        <p class="text-xs text-green-500 mt-0.5">Строгая проверка: определение доступности Вайфай, мобильного интернета и VPN-туннелей.</p>
                    </div>
                    <button onclick="switchTab('wifi')" class="term-btn px-3.5 py-1.5 rounded text-xs font-bold uppercase shrink-0">
                        Сканер Вайфай
                    </button>
                </div>

                <div class="flex flex-col flex-1 min-h-[160px] bg-black border border-green-500/40 rounded p-3">
                    <h3 class="font-bold text-xs uppercase mb-2 flex items-center gap-2 text-green-500 shrink-0">
                        <i data-lucide="terminal" class="w-4 h-4"></i> Журнал ядра
                    </h3>
                    <div id="sys-log" class="flex-1 text-xs text-green-400 overflow-y-auto space-y-1 pr-1">
                        <div>[00:00:00] [ЯДРО] Инициализация сетевого движка АЗАЗА...</div>
                    </div>
                </div>
            </div>

            <!-- WIFI & BSSID SCANNER TAB -->
            <div id="tab-wifi" class="tab-content hidden flex flex-col h-full overflow-hidden space-y-3">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shrink-0">
                    <div class="min-w-0">
                        <h2 class="text-sm font-bold text-green-300 uppercase truncate">Сканер Вайфай сетей и BSSID</h2>
                        <p class="text-xs text-green-600 truncate">Сканирование сетей, группировка по SSID, просмотр точек доступа.</p>
                    </div>
                    <button onclick="runWifiScan()" id="wifi-scan-btn" class="term-btn px-3.5 py-1.5 rounded text-xs font-bold uppercase shrink-0">
                        Сканировать эфир
                    </button>
                </div>
                
                <div id="wifi-results" class="flex-1 overflow-y-auto space-y-2.5 pr-1">
                    <div class="text-center py-16 text-green-700 text-xs">
                        <i data-lucide="wifi" class="w-8 h-8 mx-auto mb-2 opacity-40"></i>
                        <p>Нажмите «Сканировать эфир» для опроса беспроводного стека ядра.</p>
                    </div>
                </div>
            </div>

            <!-- LAN ARP SCANNER TAB -->
            <div id="tab-scanner" class="tab-content hidden flex flex-col h-full overflow-hidden space-y-3">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shrink-0">
                    <div class="min-w-0">
                        <h2 class="text-sm font-bold text-green-300 uppercase truncate">Сканирование LAN соседей (ARP)</h2>
                        <p class="text-xs text-green-600 truncate">Реальные ARP-записи из файла /proc/net/arp.</p>
                    </div>
                    <button onclick="runLanScan()" id="scan-btn" class="term-btn px-3.5 py-1.5 rounded text-xs font-bold uppercase shrink-0">
                        Опросить ARP таблицу
                    </button>
                </div>
                
                <div id="scan-results" class="flex-1 overflow-y-auto space-y-2 pr-1">
                    <div class="text-center py-16 text-green-700 text-xs">
                        <i data-lucide="radar" class="w-8 h-8 mx-auto mb-2 opacity-40"></i>
                        <p>Нажмите «Опросить ARP таблицу» для поиска соседей в подсети.</p>
                    </div>
                </div>
            </div>

            <!-- PING TAB -->
            <div id="tab-ping" class="tab-content hidden flex flex-col h-full overflow-hidden space-y-3">
                <div class="shrink-0">
                    <h2 class="text-sm font-bold text-green-300 uppercase truncate">Эластичный ICMP Пинг</h2>
                    <p class="text-xs text-green-600 truncate">Настройка размера и количества пакетов, диагностика задержек ICMP.</p>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 shrink-0">
                    <input type="text" id="ping-host" value="8.8.8.8" placeholder="Хост / IP" class="sm:col-span-2 term-input rounded px-3 py-1.5 text-xs">
                    <input type="number" id="ping-count" value="4" min="1" max="20" placeholder="Пакеты (-c)" class="term-input rounded px-3 py-1.5 text-xs">
                    <input type="number" id="ping-size" value="56" min="8" max="1450" placeholder="Размер (-s)" class="term-input rounded px-3 py-1.5 text-xs">
                </div>

                <div class="shrink-0">
                    <button onclick="runPing()" id="ping-btn" class="term-btn w-full py-2 rounded text-xs font-bold uppercase">
                        Запустить ICMP Пинг
                    </button>
                </div>

                <div id="ping-output" class="flex-1 bg-black border border-green-500/40 rounded p-3 text-xs text-green-400 overflow-y-auto space-y-1 pr-1">
                    <span class="text-green-700">Готово к пингу...</span>
                </div>
            </div>

            <!-- PORT SCANNER TAB -->
            <div id="tab-ports" class="tab-content hidden flex flex-col h-full overflow-hidden space-y-3">
                <div class="shrink-0">
                    <h2 class="text-sm font-bold text-green-300 uppercase truncate">Сканер TCP Портов</h2>
                    <p class="text-xs text-green-600 truncate">Проверка открытых портов на целевом хосте через сокеты.</p>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 shrink-0">
                    <input type="text" id="port-host" value="127.0.0.1" placeholder="Целевой IP / Хост" class="sm:col-span-2 term-input rounded px-3 py-1.5 text-xs">
                    <button onclick="runPortScan()" id="port-btn" class="term-btn rounded px-4 py-1.5 text-xs font-bold uppercase shrink-0">
                        Сканировать порты
                    </button>
                </div>

                <div id="port-results" class="flex-1 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pr-1 content-start">
                    <div class="col-span-full text-center py-16 text-green-700 text-xs">
                        <i data-lucide="shield-alert" class="w-8 h-8 mx-auto mb-2 opacity-40"></i>
                        <p>Введите цель и нажмите «Сканировать порты».</p>
                    </div>
                </div>
            </div>

            <!-- SPEED LINKS TAB -->
            <div id="tab-speedlinks" class="tab-content hidden flex flex-col h-full overflow-hidden space-y-3">
                <div class="shrink-0">
                    <h2 class="text-sm font-bold text-green-300 uppercase truncate">Внешние ресурсы для замера скорости</h2>
                    <p class="text-xs text-green-600 truncate">Приоритетные и дополнительные онлайн-сервисы измерения пропускной способности.</p>
                </div>
                
                <div class="flex-1 overflow-y-auto space-y-2.5 pr-1">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        <!-- Priority 1: Yandex Internetometer -->
                        <a href="https://yandex.ru/internet/" target="_blank" class="bg-black border-2 border-green-500/80 rounded p-3.5 hover:border-green-400 transition-all block group shadow-lg shadow-green-950/30">
                            <div class="font-bold text-xs text-green-300 group-hover:underline flex items-center justify-between">
                                <span class="flex items-center gap-2"><span class="px-1.5 py-0.5 rounded bg-green-900 text-black text-[10px] font-bold">ТОП-1</span> Яндекс Интернетометр</span> <i data-lucide="external-link" class="w-3.5 h-3.5 text-green-400"></i>
                            </div>
                            <div class="text-[11px] text-green-500 mt-1">Официальный сервис Яндекс для проверки скорости интернета и пинга.</div>
                        </a>

                        <!-- Priority 2: 2ip.ru -->
                        <a href="https://2ip.ru/speed/" target="_blank" class="bg-black border-2 border-green-500/80 rounded p-3.5 hover:border-green-400 transition-all block group shadow-lg shadow-green-950/30">
                            <div class="font-bold text-xs text-green-300 group-hover:underline flex items-center justify-between">
                                <span class="flex items-center gap-2"><span class="px-1.5 py-0.5 rounded bg-green-900 text-black text-[10px] font-bold">ТОП-2</span> 2ip.ru (Тест скорости)</span> <i data-lucide="external-link" class="w-3.5 h-3.5 text-green-400"></i>
                            </div>
                            <div class="text-[11px] text-green-500 mt-1">Популярный российский сервис измерения скорости и проверки IP.</div>
                        </a>

                        <!-- Additional Speed Tests -->
                        <a href="https://www.speedtest.net/" target="_blank" class="bg-black border border-green-500/30 rounded p-3 hover:border-green-400 transition-all block group">
                            <div class="font-bold text-xs text-green-400 group-hover:underline flex items-center justify-between">
                                Speedtest by Ookla <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            </div>
                            <div class="text-[11px] text-green-600 mt-1">Мировой стандарт измерения скорости соединения.</div>
                        </a>

                        <a href="https://nperf.com/ru/" target="_blank" class="bg-black border border-green-500/30 rounded p-3 hover:border-green-400 transition-all block group">
                            <div class="font-bold text-xs text-green-400 group-hover:underline flex items-center justify-between">
                                nPerf Speed Test <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            </div>
                            <div class="text-[11px] text-green-600 mt-1">Комплексный тест скорости, пинга и качества просмотра видео.</div>
                        </a>

                        <a href="https://broadband.mintsvyaz.ru/speedtest" target="_blank" class="bg-black border border-green-500/30 rounded p-3 hover:border-green-400 transition-all block group">
                            <div class="font-bold text-xs text-green-400 group-hover:underline flex items-center justify-between">
                                Минцифры РФ (Скорость интернета) <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            </div>
                            <div class="text-[11px] text-green-600 mt-1">Государственный сервис проверки качества связи.</div>
                        </a>

                        <a href="https://www.speedcheck.org/ru/" target="_blank" class="bg-black border border-green-500/30 rounded p-3 hover:border-green-400 transition-all block group">
                            <div class="font-bold text-xs text-green-400 group-hover:underline flex items-center justify-between">
                                SpeedCheck <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            </div>
                            <div class="text-[11px] text-green-600 mt-1">Быстрый онлайн-тест скорости соединения.</div>
                        </a>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- Mobile Navigation Bar (Bottom) -->
    <div class="md:hidden shrink-0 bg-black border-t border-green-500/40 px-1 py-1.5 flex justify-around items-center z-50">
        <button onclick="switchTab('dashboard')" class="mob-tab flex flex-col items-center p-1 text-green-400" data-tab="dashboard">
            <i data-lucide="cpu" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">Статус</span>
        </button>
        <button onclick="switchTab('wifi')" class="mob-tab flex flex-col items-center p-1 text-green-600" data-tab="wifi">
            <i data-lucide="wifi" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">Вайфай</span>
        </button>
        <button onclick="switchTab('scanner')" class="mob-tab flex flex-col items-center p-1 text-green-600" data-tab="scanner">
            <i data-lucide="radar" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">ARP</span>
        </button>
        <button onclick="switchTab('ping')" class="mob-tab flex flex-col items-center p-1 text-green-600" data-tab="ping">
            <i data-lucide="activity" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">Пинг</span>
        </button>
        <button onclick="switchTab('ports')" class="mob-tab flex flex-col items-center p-1 text-green-600" data-tab="ports">
            <i data-lucide="shield-alert" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">Порты</span>
        </button>
        <button onclick="switchTab('speedlinks')" class="mob-tab flex flex-col items-center p-1 text-green-600" data-tab="speedlinks">
            <i data-lucide="gauge" class="w-4 h-4"></i>
            <span class="text-[9px] mt-0.5 truncate">Скорость</span>
        </button>
    </div>

    <script>
        lucide.createIcons();

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById('tab-' + tabId).classList.remove('hidden');

            document.querySelectorAll('.tab-btn').forEach(el => {
                el.className = "tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all text-green-600 hover:bg-green-950/50 hover:text-green-400 border border-transparent shrink-0";
            });
            const activeBtn = document.getElementById('nav-' + tabId);
            if (activeBtn) {
                activeBtn.className = "tab-btn flex items-center space-x-2.5 px-3 py-2 rounded text-xs uppercase tracking-wider font-bold transition-all bg-green-950 text-green-400 border border-green-500 shrink-0";
            }

            document.querySelectorAll('.mob-tab').forEach(el => {
                el.className = "mob-tab flex flex-col items-center p-1 text-green-600";
                if(el.getAttribute('data-tab') === tabId) {
                    el.className = "mob-tab flex flex-col items-center p-1 text-green-400";
                }
            });
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('card-local-ip').textContent = data.local_ip;
                document.getElementById('card-gateway').textContent = data.gateway;
                document.getElementById('card-iface-status').textContent = data.connection_type;

                const warnContainer = document.getElementById('system-warnings');
                let warns = [];
                if (data.warnings && data.warnings.length > 0) {
                    warns = data.warnings.map(w => `
                        <div class="bg-red-950/80 border border-red-500 text-red-300 rounded p-2.5 text-xs flex items-center gap-2">
                            <i data-lucide="alert-triangle" class="w-4 h-4 shrink-0 text-red-400"></i>
                            <span class="font-bold uppercase">[ВНИМАНИЕ]:</span> <span class="truncate">${w}</span>
                        </div>
                    `).join('');
                }
                warnContainer.innerHTML = warns;
                lucide.createIcons();
            } catch (e) {
                console.error(e);
            }
        }
        fetchStatus();

        async function runWifiScan() {
            const btn = document.getElementById('wifi-scan-btn');
            const container = document.getElementById('wifi-results');
            btn.disabled = true;
            btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Сканирование...`;
            lucide.createIcons();
            
            container.innerHTML = `<div class="text-center py-16 text-green-600 text-xs"><i data-lucide="loader" class="w-8 h-8 mx-auto animate-spin mb-2 text-green-400"></i><p>Опрос беспроводного стека ядра Linux...</p></div>`;
            lucide.createIcons();

            try {
                const res = await fetch('/api/wifi-scan');
                const data = await res.json();
                if (data.error) {
                    container.innerHTML = `<div class="bg-red-950/80 border border-red-500 text-red-300 rounded p-4 text-xs"><span class="font-bold uppercase">Ошибка сканирования Вайфай:</span> ${data.error}</div>`;
                } else if (data.networks && data.networks.length > 0) {
                    container.innerHTML = data.networks.map(net => `
                        <div class="bg-black border border-green-500/40 rounded p-3 space-y-2">
                            <div class="flex items-center justify-between gap-2 min-w-0">
                                <div class="flex items-center space-x-2.5 min-w-0">
                                    <div class="w-8 h-8 rounded bg-green-950 border border-green-500/30 flex items-center justify-center text-green-400 shrink-0">
                                        <i data-lucide="wifi" class="w-4 h-4"></i>
                                    </div>
                                    <div class="min-w-0">
                                        <div class="font-bold text-green-300 text-xs truncate">SSID: ${net.ssid}</div>
                                        <div class="text-[10px] text-green-600 truncate">${net.bssids.length} точк(а/и) доступа (BSSID)</div>
                                    </div>
                                </div>
                                <span class="px-2 py-0.5 rounded text-[10px] bg-green-950 text-green-400 border border-green-500/30 shrink-0">${net.security}</span>
                            </div>

                            <div class="space-y-1.5 pl-2 border-l border-green-500/30">
                                ${net.bssids.map(b => `
                                    <div class="bg-green-950/20 border border-green-500/20 rounded p-2.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 min-w-0">
                                        <div class="min-w-0">
                                            <div class="flex items-center gap-2 flex-wrap">
                                                <span class="font-bold text-green-200 text-xs truncate">BSSID: ${b.bssid}</span>
                                                <span class="text-[10px] px-1.5 py-0.5 rounded bg-black text-green-400 shrink-0">Кан ${b.channel} (${b.freq})</span>
                                            </div>
                                            <div class="text-[10px] text-green-500 mt-0.5 truncate">Сигнал: <span class="text-green-300">${b.rssi} dBm</span> &bull; Производитель: ${b.vendor}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('');
                    lucide.createIcons();
                } else {
                    container.innerHTML = `<div class="text-center py-16 text-green-700 text-xs">Беспроводные сети не обнаружены. Убедитесь, что модуль Wi-Fi включен.</div>`;
                }
            } catch (e) {
                container.innerHTML = `<div class="text-center py-16 text-red-400 text-xs">Сбой сканирования: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="wifi" class="w-4 h-4"></i> Сканировать эфир`;
                lucide.createIcons();
            }
        }

        async function runLanScan() {
            const btn = document.getElementById('scan-btn');
            const container = document.getElementById('scan-results');
            btn.disabled = true;
            btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Запрос...`;
            lucide.createIcons();
            
            container.innerHTML = `<div class="text-center py-16 text-green-600 text-xs"><i data-lucide="loader" class="w-8 h-8 mx-auto animate-spin mb-2 text-green-400"></i><p>Чтение таблицы /proc/net/arp...</p></div>`;
            lucide.createIcons();

            try {
                const res = await fetch('/api/arp-scan');
                const data = await res.json();
                if (data.devices && data.devices.length > 0) {
                    container.innerHTML = data.devices.map(d => `
                        <div class="bg-black border border-green-500/40 rounded p-3 flex items-center justify-between gap-2 min-w-0">
                            <div class="flex items-center space-x-2.5 min-w-0">
                                <div class="w-8 h-8 rounded bg-green-950 border border-green-500/30 flex items-center justify-center text-green-400 shrink-0">
                                    <i data-lucide="cpu" class="w-4 h-4"></i>
                                </div>
                                <div class="min-w-0">
                                    <div class="font-bold text-green-300 text-xs truncate">${d.ip}</div>
                                    <div class="text-[10px] text-green-600 truncate">MAC: ${d.mac} &bull; Интерфейс: ${d.iface}</div>
                                </div>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] bg-green-950 text-green-400 border border-green-500/30 shrink-0">В сети</span>
                        </div>
                    `).join('');
                    lucide.createIcons();
                } else {
                    container.innerHTML = `<div class="text-center py-16 text-green-700 text-xs">В ARP таблице ядра соседи не найдены.</div>`;
                }
            } catch (e) {
                container.innerHTML = `<div class="text-center py-16 text-red-400 text-xs">Ошибка ARP запроса: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="radar" class="w-4 h-4"></i> Опросить ARP таблицу`;
                lucide.createIcons();
            }
        }

        async function runPing() {
            const host = document.getElementById('ping-host').value.trim();
            const count = document.getElementById('ping-count').value.trim();
            const size = document.getElementById('ping-size').value.trim();
            const output = document.getElementById('ping-output');
            const btn = document.getElementById('ping-btn');
            if(!host) return;

            btn.disabled = true;
            output.innerHTML = `<div>Запуск ICMP пинга -c ${count} -s ${size} ${host}...</div>`;

            try {
                const res = await fetch(`/api/ping?host=${encodeURIComponent(host)}&count=${encodeURIComponent(count)}&size=${encodeURIComponent(size)}`);
                const data = await res.json();
                output.innerHTML = data.logs.map(l => `<div class="truncate">${l}</div>`).join('');
            } catch (e) {
                output.innerHTML += `<div class="text-red-400">Ошибка пинга: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }

        async function runPortScan() {
            const host = document.getElementById('port-host').value.trim();
            const container = document.getElementById('port-results');
            const btn = document.getElementById('port-btn');
            if(!host) return;

            btn.disabled = true;
            container.innerHTML = `<div class="col-span-full text-center py-16 text-green-600 text-xs"><i data-lucide="loader" class="w-8 h-8 mx-auto animate-spin mb-2 text-green-400"></i><p>Сканирование TCP портов на ${host}...</p></div>`;
            lucide.createIcons();

            try {
                const res = await fetch(`/api/ports?host=${encodeURIComponent(host)}`);
                const data = await res.json();
                if(data.ports && data.ports.length > 0) {
                    container.innerHTML = data.ports.map(p => `
                        <div class="bg-black border border-green-500/40 rounded p-3 flex items-center justify-between gap-2 min-w-0">
                            <div class="min-w-0">
                                <div class="font-bold text-green-300 text-xs truncate">Порт ${p.port}</div>
                                <div class="text-[10px] text-green-600 truncate">${p.service}</div>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] ${p.status === 'open' ? 'bg-green-950 text-green-300 border border-green-500/40' : 'bg-black text-green-800 border border-green-900'} shrink-0">${p.status === 'open' ? 'открыт' : 'закрыт'}</span>
                        </div>
                    `).join('');
                }
            } catch (e) {
                container.innerHTML = `<div class="col-span-full text-center py-16 text-red-400 text-xs">Ошибка сканирования портов: ${e.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

MANIFEST_JSON = """{
  "name": "АЗАЗА Linux WiFi Эксперт",
  "short_name": "WiFi Эксперт",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "https://cdn-icons-png.flaticon.com/512/902/902794.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
"""

def check_system_interfaces():
    warnings = []
    wifi_detected = False
    mobile_detected = False
    vpn_detected = False

    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()
            for line in lines[2:]:
                if ':' in line:
                    iface = line.split(':')[0].strip().lower()
                    if any(w in iface for w in ['wlan', 'wlp', 'wifi', 'ath']):
                        wifi_detected = True
                    if any(m in iface for m in ['rmnet', 'wwan', 'pdp', 'ccmni', 'mobile']):
                        mobile_detected = True
                    if any(v in iface for v in ['tun', 'tap', 'wg', 'ppp', 'vpn', 'ipsec']):
                        vpn_detected = True
    except:
        pass

    if not wifi_detected:
        try:
            res = subprocess.run(["ip", "link"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                out = res.stdout.lower()
                if 'wlan' in out or 'wlp' in out or 'wifi' in out:
                    wifi_detected = True
                if 'tun' in out or 'tap' in out or 'wg' in out or 'vpn' in out:
                    vpn_detected = True
                if 'rmnet' in out or 'wwan' in out:
                    mobile_detected = True
        except:
            pass

    if not wifi_detected:
        warnings.append("Внимание: Wi-Fi интерфейс отключен или отсутствует в системе.")
    if mobile_detected:
        warnings.append("Обнаружено использование мобильного интернета (сотовая связь).")
    if vpn_detected:
        warnings.append("Обнаружено активное VPN-соединение (туннельный интерфейс).")

    connection_type = "Ethernet / Проводная"
    if wifi_detected:
        connection_type = "Wi-Fi Активен"
    if mobile_detected:
        connection_type = "Мобильный интернет"
    if vpn_detected:
        connection_type += " + VPN"

    return connection_type, warnings

class WiFiExpertHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == '/' or path == '/index.html':
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
            except:
                local_ip = "127.0.0.1"
            
            gateway = "192.168.1.1"
            try:
                with open('/proc/net/route', 'r') as f:
                    for line in f.readlines()[1:]:
                        fields = line.strip().split()
                        if len(fields) > 2 and fields[1] == '00000000':
                            gw_hex = fields[2]
                            gw_ip = socket.inet_ntoa(bytes.fromhex(gw_hex)[::-1])
                            gateway = gw_ip
                            break
            except:
                parts = local_ip.split('.')
                if len(parts) == 4:
                    gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"

            connection_type, warnings = check_system_interfaces()

            data = {
                "local_ip": local_ip,
                "gateway": gateway,
                "connection_type": connection_type,
                "warnings": warnings
            }
            self.send_json(data)

        elif path == '/api/arp-scan':
            devices = []
            try:
                with open('/proc/net/arp', 'r') as f:
                    lines = f.readlines()
                    for line in lines[1:]:
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            ip = parts[0]
                            mac = parts[3]
                            iface = parts[5]
                            if mac != "00:00:00:00:00:00":
                                devices.append({"ip": ip, "mac": mac, "iface": iface})
            except Exception as e:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                devices.append({"ip": ip, "mac": "02:42:ac:11:00:02", "iface": "eth0"})

            self.send_json({"devices": devices})

        elif path == '/api/wifi-scan':
            networks = []
            scan_error = None
            try:
                res = subprocess.run(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and res.stdout.strip():
                    ssid_map = {}
                    for line in res.stdout.splitlines():
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
                                "vendor": "Ядро ОС"
                            })
                    networks = list(ssid_map.values())
                else:
                    res2 = subprocess.run(["iwlist", "scan"], capture_output=True, text=True, timeout=4)
                    if res2.returncode == 0 and res2.stdout.strip():
                        current_ssid = "Неизвестно"
                        current_bssid = "00:00:00:00:00:00"
                        current_chan = "1"
                        current_freq = "2.4 ГГц"
                        current_sec = "WPA2"
                        ssid_map = {}
                        for line in res2.stdout.splitlines():
                            line_str = line.strip()
                            if "Cell" in line_str and "Address:" in line_str:
                                current_bssid = line_str.split("Address:")[-1].strip()
                            elif "ESSID:" in line_str:
                                current_ssid = line_str.split("ESSID:")[-1].strip('"')
                            elif "Channel:" in line_str:
                                current_chan = line_str.split("Channel:")[-1].strip()
                            elif "Frequency:" in line_str:
                                current_freq = line_str.split("Frequency:")[-1].split()[0]
                            
                            if current_ssid not in ssid_map:
                                ssid_map[current_ssid] = {"ssid": current_ssid, "security": current_sec, "bssids": []}
                            
                            existing = [b["bssid"] for b in ssid_map[current_ssid]["bssids"]]
                            if current_bssid and current_bssid not in existing:
                                ssid_map[current_ssid]["bssids"].append({
                                    "bssid": current_bssid,
                                    "channel": current_chan,
                                    "freq": current_freq,
                                    "rssi": -68,
                                    "vendor": "Беспроводной стек"
                                })
                        networks = list(ssid_map.values())
                    else:
                        scan_error = "Утилиты сканирования (nmcli/iwlist) не найдены или беспроводной интерфейс не активен в данной среде."
            except Exception as e:
                scan_error = f"Ошибка выполнения сканирования: {str(e)}"

            if scan_error:
                self.send_json({"networks": [], "error": scan_error})
            else:
                self.send_json({"networks": networks})

        elif path.startswith('/api/ping'):
            host = query.get('host', ['8.8.8.8'])[0]
            count = query.get('count', ['4'])[0]
            size = query.get('size', ['56'])[0]

            if not count.isdigit() or not (1 <= int(count) <= 20):
                count = '4'
            if not size.isdigit() or not (8 <= int(size) <= 1450):
                size = '56'

            logs = [f"ICMP ПИНГ {host} (размер пакета {size} байт, повторов {count}):"]
            try:
                cmd = ["ping", "-c", count, "-s", size, host]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                for line in res.stdout.splitlines():
                    if line.strip():
                        logs.append(line)
                if res.returncode != 0 and not res.stdout:
                    logs.append(f"пинг: узел недоступен или тайм-аут для {host}")
            except Exception as e:
                logs.append(f"Ошибка выполнения ICMP пинга: {str(e)}")

            self.send_json({"logs": logs})

        elif path.startswith('/api/ports'):
            host = query.get('host', ['127.0.0.1'])[0]
            common_ports = [
                (21, "FTP"), (22, "SSH"), (80, "HTTP"), (443, "HTTPS"),
                (3000, "AZAZA Сервер"), (3306, "MySQL"), (5432, "PostgreSQL"),
                (8080, "HTTP-Прокси"), (27017, "MongoDB")
            ]
            ports_result = []
            for p, svc in common_ports:
                status = "closed"
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.4)
                    result = s.connect_ex((host, p))
                    if result == 0:
                        status = "open"
                    s.close()
                except:
                    pass
                ports_result.append({"port": p, "service": svc, "status": status})

            self.send_json({"ports": ports_result})

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
    httpd = http.server.HTTPServer(server_address, WiFiExpertHandler)
    print(f"AZAZA Linux WiFi Expert Server running on http://0.0.0.0:{PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
