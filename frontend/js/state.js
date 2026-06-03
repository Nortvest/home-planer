function toDateStr(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function parseDateStr(dateStr) {
    const [y, m, d] = dateStr.split('-').map(Number);
    return new Date(y, m - 1, d);
}

const today = new Date();
const todayDow = today.getDay();
const weekStartOffset = todayDow === 0 ? -6 : 1 - todayDow;
const weekStart = new Date(today);
weekStart.setDate(today.getDate() + weekStartOffset);
weekStart.setHours(0, 0, 0, 0);

const state = {
    currentYear: today.getFullYear(),
    currentMonth: today.getMonth() + 1,
    currentWeekStart: toDateStr(weekStart),
    users: [],
    calendarTasks: {},
    lastLoadedMonth: null,
    lastLoadedWeek: null,
    monthOverviewYear: null,
    monthOverviewMonth: null,
    monthOverviewDays: null,
};

export function setUsers(users) {
    state.users = [...users];
}

export function getUsers() {
    return [...state.users];
}

export function setCurrentMonth(year, month) {
    state.currentYear = year;
    state.currentMonth = month;
    state.lastLoadedMonth = `${year}-${month}`;
}

export function getCurrentMonth() {
    return { year: state.currentYear, month: state.currentMonth };
}

export function setCalendarTasks(monthKey, tasks) {
    state.calendarTasks[monthKey] = tasks;
}

export function getCalendarTasks(year, month) {
    const key = `${year}-${month}`;
    const tasks = state.calendarTasks[key];
    return tasks ? [...tasks] : null;
}

export function updateTaskInState(year, month, taskId, updater) {
    const key = `${year}-${month}`;
    const days = state.calendarTasks[key];
    if (!days) return false;
    for (const dateKey of Object.keys(days)) {
        const tasks = days[dateKey];
        for (const task of tasks) {
            if (task.id === taskId) {
                updater(task);
                return true;
            }
        }
    }
    return false;
}

export function clearCalendarCache() {
    state.calendarTasks = {};
    state.lastLoadedMonth = null;
    state.lastLoadedWeek = null;
    state.monthOverviewYear = null;
    state.monthOverviewMonth = null;
    state.monthOverviewDays = null;
}

export function setWeekStart(dateStr) {
    state.currentWeekStart = dateStr;
    const d = parseDateStr(dateStr);
    state.currentYear = d.getFullYear();
    state.currentMonth = d.getMonth() + 1;
    if (d.getDate() <= 3) {
        const prevMonth = d.getMonth();
        state.currentMonth = prevMonth + 1;
        state.currentYear = prevMonth === 0 ? d.getFullYear() - 1 : d.getFullYear();
    }
}

export function getWeekStart() {
    return state.currentWeekStart;
}

export function setLastLoadedWeek(dateStr) {
    state.lastLoadedWeek = dateStr;
}

export function getLastLoadedWeek() {
    return state.lastLoadedWeek;
}

export function getWeekRange() {
    const start = parseDateStr(state.currentWeekStart);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return {
        start: state.currentWeekStart,
        end: toDateStr(end),
    };
}

export function setWeekTasks(weekStart, daysData) {
    state.calendarTasks[`week:${weekStart}`] = daysData;
}

export function getWeekTasks(weekStart) {
    const data = state.calendarTasks[`week:${weekStart}`];
    return data || null;
}

export function setMonthOverview(year, month, daysData) {
    state.monthOverviewYear = year;
    state.monthOverviewMonth = month;
    state.monthOverviewDays = daysData;
}

export function getMonthOverview() {
    return {
        year: state.monthOverviewYear,
        month: state.monthOverviewMonth,
        days: state.monthOverviewDays,
    };
}

export function updateTaskInWeekState(weekStart, taskId, updater) {
    const key = `week:${weekStart}`;
    const days = state.calendarTasks[key];
    if (!days) return false;
    for (const dateKey of Object.keys(days)) {
        const tasks = days[dateKey];
        for (const task of tasks) {
            if (task.id === taskId) {
                updater(task);
                return true;
            }
        }
    }
    return false;
}
