GLClient.controller('UserCtrl',
  ['$scope', '$rootScope', '$location', 'WhistleblowerTip',
  function($scope, $rootScope, $location, WhistleblowerTip) {

  $scope.$watch("language", function (newVal, oldVal) {
    if (newVal && newVal !== oldVal) {
      $rootScope.language = $scope.language;
    }
  });

  $scope.view_tip = function(keycode) {
    keycode = keycode.replace(/\D/g,'');
    var wtip = new WhistleblowerTip(keycode, function() {
      $location.path('/status');
    });
  };
}]);

GLClient.controller('ForcedPasswordChangeCtrl', ['$scope', '$rootScope', '$location', 'changePasswordWatcher', 'Authentication',
  function($scope, $rootScope, $location, changePasswordWatcher, Authentication) {

    changePasswordWatcher($scope, "preferences.old_password",
        "preferences.password", "preferences.check_password");

    $scope.pass_save = function () {
      // avoid changing any PGP setting
      $scope.preferences.pgp_key_remove = false;
      $scope.preferences.pgp_key_public = '';

      $scope.preferences.$update(function () {
        if (!$rootScope.successes) {
          $rootScope.successes = [];
        }

        $rootScope.successes.push({message: 'Updated your password!'});

        $location.path(Authentication.auth_landing_page);
      });
    };
}]);
