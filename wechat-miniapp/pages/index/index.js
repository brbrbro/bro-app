const auth = require('../../utils/auth.js');
const i18n = require('../../utils/i18n.js');

Page({
  data: {
    // 系统信息
    statusBarHeight: 0,
    
    // 用户数据
    userInfo: null,
    isLoggedIn: false,
    
    // 个人中心展开状态
    profileOpen: false,
    
    // 用户等级和经验
    userLevel: 1,
    userExp: 0,
    maxExp: 100,
    userPoints: 0,
    isMember: false,
    hasSignedIn: false,
    
    // 菜单面板展开状态
    menuOpen: false,
    
    // 选择区域展开状态
    showSelector: false,
    
    // 语言选择器
    showLanguagePicker: false,
    languages: [
      { key: 'zh', label: '简体中文' },
      { key: 'zht', label: '繁體中文' },
      { key: 'en', label: 'English' }
    ],
    currentLanguage: 'zh',
    currentLanguageLabel: '简体中文',
    
    // 翻译文本
    t: {},
    
    // 原来的首页数据
    region: 'hk',
    subjects: [],
    selectedSubject: null
  },

  onLoad() {
    const windowInfo = wx.getWindowInfo();
    const currentLang = i18n.getCurrentLanguage();
    this.setData({ 
      statusBarHeight: windowInfo.safeArea.top,
      currentLanguage: currentLang.key,
      currentLanguageLabel: currentLang.label,
      t: this.getTranslations()
    });
    this.loadSubjects();
    this.loadUserData();
  },
  
  getTranslations() {
    return {
      appName: i18n.t('appName'),
      selectExamSubject: i18n.t('selectExamSubject'),
      gaokao: i18n.t('gaokao'),
      dse: i18n.t('dse'),
      // 六大功能按钮
      myStats: i18n.t('myStats'),
      myQuestions: i18n.t('myQuestions'),
      myBag: i18n.t('myBag'),
      myClassmates: i18n.t('myClassmates'),
      inviteClassmates: i18n.t('inviteClassmates'),
      myMembership: i18n.t('myMembership'),
      level: i18n.t('level'),
      exp: i18n.t('exp'),
      points: i18n.t('points'),
      signIn: i18n.t('signIn'),
      signedIn: i18n.t('signedIn'),
      guest: i18n.t('guest'),
      menu: i18n.t('menu'),
      notifications: i18n.t('notifications'),
      difficultyPreference: i18n.t('difficultyPreference'),
      scan: i18n.t('scan'),
      language: i18n.t('language'),
      settings: i18n.t('settings')
    };
  },
  
  updateTranslations() {
    const currentLang = i18n.getCurrentLanguage();
    this.setData({ 
      t: this.getTranslations(),
      currentLanguage: currentLang.key,
      currentLanguageLabel: currentLang.label
    });
  },

  onShow() {
    this.loadUserData();
  },

  loadUserData() {
    const userInfo = auth.getUserInfo();
    const isLoggedIn = auth.isLoggedIn();
    
    this.setData({
      userInfo,
      isLoggedIn,
      userLevel: isLoggedIn ? 5 : 1,
      userExp: isLoggedIn ? 75 : 0,
      maxExp: 100,
      userPoints: isLoggedIn ? 1280 : 0,
      isMember: isLoggedIn && userInfo && userInfo.member_type === 'premium'
    });
  },

  // 个人中心展开/收起
  toggleProfile() {
    this.setData({ 
      profileOpen: !this.data.profileOpen,
      menuOpen: false,
      showSelector: false
    });
  },

  closeProfile() {
    this.setData({ profileOpen: false });
  },

  // 菜单展开/收起
  toggleMenu() {
    this.setData({ 
      menuOpen: !this.data.menuOpen,
      profileOpen: false,
      showSelector: false
    });
  },

  closeMenu() {
    this.setData({ menuOpen: false });
  },

  // 选择区域展开/收起
  toggleSelector() {
    this.setData({ 
      showSelector: !this.data.showSelector,
      profileOpen: false,
      menuOpen: false
    });
  },

  // 签到
  signIn() {
    if (this.data.hasSignedIn) {
      wx.showToast({ title: '今日已签到', icon: 'none' });
      return;
    }
    
    const newPoints = this.data.userPoints + 10;
    const newExp = this.data.userExp + 5;
    
    this.setData({
      userPoints: newPoints,
      userExp: newExp,
      hasSignedIn: true
    });
    
    wx.showToast({
      title: '签到成功 +10积分',
      icon: 'success'
    });
  },

  // 导航到各页面
  goMyStats() {
    wx.navigateTo({ url: '/pages/stats/stats' });
  },

  goMyQuestions() {
    wx.navigateTo({ url: '/pages/myquestions/myquestions' });
  },

  goMyBag() {
    wx.navigateTo({ url: '/pages/mybag/mybag' });
  },

  goMyClassmates() {
    wx.navigateTo({ url: '/pages/classmates/classmates' });
  },

  goInvite() {
    wx.navigateTo({ url: '/pages/invite/invite' });
  },

  goMyMembership() {
    wx.navigateTo({ url: '/pages/membership/membership' });
  },

  // 设置菜单功能
  goNotifications() {
    wx.showToast({ title: '通知中心', icon: 'none' });
  },

  goDifficulty() {
    wx.showToast({ title: '难度偏好', icon: 'none' });
  },

  goScan() {
    wx.scanCode({
      success: (res) => {
        console.log('扫码结果:', res);
      }
    });
  },

  switchLanguage() {
    this.setData({ 
      showLanguagePicker: true,
      menuOpen: false
    });
  },
  
  closeLanguagePicker() {
    this.setData({ showLanguagePicker: false });
  },
  
  selectLanguage(e) {
    const lang = e.currentTarget.dataset.lang;
    i18n.setLanguage(lang);
    this.updateTranslations();
    this.setData({ showLanguagePicker: false });
    wx.showToast({ 
      title: i18n.t('language') + ' OK', 
      icon: 'success' 
    });
  },

  goSettings() {
    wx.showToast({ title: '系统设置', icon: 'none' });
  },

  // 六大功能按钮
  goQuestionBank() {
    wx.switchTab({ url: '/pages/index/index' });
  },
  
  goDailyChallenge() {
    wx.navigateTo({ url: '/pages/daily-challenge/daily-challenge' });
  },
  
  goCreateQuestion() {
    wx.navigateTo({ url: '/pages/import/import' });
  },
  
  goWrongBook() {
    wx.switchTab({ url: '/pages/wrongbook/wrongbook' });
  },
  
  goLeaderboard() {
    wx.navigateTo({ url: '/pages/leaderboard/leaderboard' });
  },
  
  goPointsShop() {
    wx.showToast({ title: '积分商城', icon: 'none' });
  },

  goLiCiTong() {
    wx.showToast({ title: '理词通', icon: 'none' });
  },

  // 底部导航栏按钮
  goSquare() {
    wx.showToast({ title: '广场', icon: 'none' });
  },
  
  goStudyRoom() {
    wx.showToast({ title: '自习室', icon: 'none' });
  },
  
  goPracticePage() {
    wx.switchTab({ url: '/pages/practice/practice' });
  },

  // 原来的首页逻辑
  switchRegion(e) {
    const region = e.currentTarget.dataset.region;
    this.setData({ region });
    this.loadSubjects();
  },

  loadSubjects() {
    const region = this.data.region;
    const subjectMap = {
      mainland: ['数学', '物理', '化学', '生物'],
      hk: ['数学', '物理', '化学', '生物']
    };
    this.setData({ subjects: subjectMap[region] || [] });
  },

  selectSubject(e) {
    const subject = e.currentTarget.dataset.subject;
    this.setData({ 
      selectedSubject: subject,
      showSelector: false 
    });
  }
});
