define((require, exports, module) => {
  const gui = require('UiDat')
  const storeManager = require('State')
  const robotStore = require('Robot')

  const geometry = storeManager.getStore('Robot').getState().geometry
  const jointLimits = storeManager.getStore('Robot').getState().jointLimits

  const robotGuiStore = storeManager.createStore('RobotGui', {})


  const DEG_TO_RAD = Math.PI / 180
  const RAD_TO_DEG = 180 / Math.PI
  /* DAT GUI */

  const geometryGui = gui.addFolder('robot geometry')

  for (const link in geometry) {
    if (link) {
      const linkFolder = geometryGui.addFolder(`link ${link}`)
      for (const axis in geometry[link]) {
        if (axis) {
          gui.remember(geometry[link])
          linkFolder.add(geometry[link], axis).min(-10).max(10).step(0.1).onChange(() => {
            robotStore.dispatch('ROBOT_CHANGE_GEOMETRY', geometry)
          })
        }
      }
    }
  }

  const anglesDeg = {
    A0: 0,
    A1: 0,
    A2: 0,
    A3: 0,
    A4: 0,
    A5: 0,
  }

  const configuration = {
    1: false,
    2: false,
    3: false,
  }

  const jointLimitsDeg = {
    J0: [-190, 190],
    J1: [-58, 90],
    J2: [-135, 40],
    J3: [-90, 75],
    J4: [-139, 20],
    J5: [-188, 181],
  }

  robotStore.listen([state => state.angles], (angles) => {
    Object.keys(anglesDeg).forEach((k) => {
      anglesDeg[k] = angles[k] / Math.PI * 180
    })
  })

  const anglesGui = gui.addFolder('angles')
  let i = 0
  for (const key in anglesDeg) {
    anglesGui.add(anglesDeg, key).min(jointLimits[`J${i}`][0] * RAD_TO_DEG).max(jointLimits[`J${i++}`][1] * RAD_TO_DEG).step(1).listen().onChange(() => {
      const anglesRad = {}
      for (const key in anglesDeg) {
        if (anglesDeg.hasOwnProperty(key)) {
          anglesRad[key] = anglesDeg[key] * DEG_TO_RAD
        }
      }
      robotStore.dispatch('ROBOT_CHANGE_ANGLES', anglesRad)
    })
  }

  const configurationGui = gui.addFolder('configuration')
  for (const key in configuration) {
    configurationGui.add(configuration, key).listen().onChange(() => {
      robotStore.dispatch('ROBOT_CHANGE_CONFIGURATION', Object.values(configuration))
    })
  }

  const angleLimitGui = anglesGui.addFolder('angle limits')
  for (const joint in jointLimitsDeg) {
    if (joint) {
      const jointFolder = angleLimitGui.addFolder(`joint ${joint}`)
      for (const limit in jointLimitsDeg[joint]) {
        if (limit) {
          // gui.remember(jointLimitsDeg[joint])

          (j => jointFolder.add(jointLimitsDeg[j], limit).name((limit == 0) ? 'min' : 'max').min(-360).max(360).step(1).onChange(() => {
            limts_rad = {}
            limts_rad[j] = [
              jointLimitsDeg[j][0] * DEG_TO_RAD,
              jointLimitsDeg[j][1] * DEG_TO_RAD,
            ]
            robotStore.dispatch('ROBOT_CHANGE_JOINT_LIMITS', limts_rad)
          }))(joint)
        }
      }
    }
  }

  /* END DAT GUI */

  module.exports = robotStore

  // --- Python API polling integration ---
  // Poll the Python server every second and update robot angles
  setInterval(() => {
    fetch('http://localhost:5050/joints')
      .then(res => res.json())
      .then(joints => {
        console.log('Fetched joints:', joints); // Debug log
        if (!Array.isArray(joints) || joints.length !== 6) return;
        // Convert to radians and dispatch to robotStore
        const anglesRad = {
          A0: joints[0] * Math.PI / 180,
          A1: joints[1] * Math.PI / 180,
          A2: joints[2] * Math.PI / 180,
          A3: joints[3] * Math.PI / 180,
          A4: joints[4] * Math.PI / 180,
          A5: joints[5] * Math.PI / 180,
        };
        robotStore.dispatch('ROBOT_CHANGE_ANGLES', anglesRad);
        console.log('Dispatched angles:', anglesRad); // Debug log
      })
      .catch(err => {
        // Optionally log error or ignore if server is not running
        console.error('Python API fetch error:', err); // Debug log
      });
  }, 1000);
  // --- End Python API polling integration ---
})
