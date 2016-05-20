# Fil's Third Person Camera
# by Filippo Bovo
#
# (Tested with Blender 2.76)

import bge
import mathutils
import math

# Colors
Red = (255,0,0)
Green = (0,255,0)
Blue = (0,0,255)
Magenta = (255, 0, 255)
Yellow = (255,255,0)

# Debug variable
debugState = 0

# Camera parameters
# See, for example, https://en.wikipedia.org/wiki/Spherical_coordinate_system for definition and nomenclature of spherical coordinates (note that Theta and Phi are sometimes defined in the opposite way)
Phi = 0.0 # Initial azimuthal angle, 0 < Phi < 2*Pi
Theta = 0.0 # Initial polar angle, -Pi/2 < Theta < Pi/2
Theta_max = 1.5 # Constraint: max polar angle, Theta_min < Theta_max < Pi/2
Theta_min = -1.5 # Constraint: min polar angle, -Pi/2 < Theta_min < Theta_max
R = 2.0 # Initial radius, R_min < R < R_max
R_max = 3.0 # Constraint: max radius, R_min < R_max
R_min = 0.5 # Constraint: min radius, 0.0 < R_min < R_max
Gamma_c_a = 0.9 # Angular damping coefficient, 0.0 < Gamma_c_a < 1.0
Gamma_c_r = 0.95 # Radial damping coefficient, 0.0 < Gamma_c_r < 1.0
Gamma_t = 0.1 # Damping coefficient of the angle towards the subject, 0.0 < Gamma_c_t < 1.0


# Input
# Sensitivity
mouseX_sens = 0.01
mouseY_sens = 0.01
# Window parameters
width = bge.render.getWindowWidth()
height = bge.render.getWindowHeight()
# Mouse parameters
mouseX = (bge.logic.mouse.position[0] * width - width//2) * mouseX_sens
mouseY = (height//2 - bge.logic.mouse.position[1] * height) * mouseY_sens
if abs(mouseX) > 0.00001 or abs(mouseY) > 0.00001: # Fix Mouse Lag
    bge.render.setMousePosition(width//2, height//2) # Reset mouse position
# Fake mouse wheel with "n" and "m" keys
mouseWheel = 0.0
if bge.logic.KX_INPUT_ACTIVE == bge.logic.mouse.events[bge.events.WHEELUPMOUSE]:
    mouseWheel = -0.5
if bge.logic.KX_INPUT_ACTIVE == bge.logic.mouse.events[bge.events.WHEELDOWNMOUSE]:
    mouseWheel = 0.5

def main():

    # BGE objects
    cont = bge.logic.getCurrentController()
    owner = cont.owner
    keyboard = bge.logic.keyboard
    scene = bge.logic.getCurrentScene()

   #init(owner, scene,  phi, theta, theta_max, theta_min, r,   r_max, r_min, gamma_c_a, gamma_c_r, gamma_t)
    init(owner, scene,  Phi, Theta, Theta_max, Theta_min, R,   R_max, R_min, Gamma_c_a, Gamma_c_r, Gamma_t)
    update_camera(owner, mouseX, mouseY, mouseWheel)

def init(owner, scene, phi, theta, theta_max, theta_min, r, r_max, r_min, gamma_c_a, gamma_c_r, gamma_t):
    if 'init' not in owner:
        # Spherical coordinates of the camera system
        owner['phi'] = phi # Angle between 0 and 2*Pi
        owner['theta'] = theta # Angle between -theta_max and theta_max.
        owner['theta_max'] = theta_max # Max value of theta. It must be between Min and pi.
        owner['theta_min'] = theta_min # Min value of theta. It must be between 0 and Max.
        owner['r'] = r # Distance from center
        owner['r_max'] = r_max # Max value of r. It must be greater than Min.
        owner['r_min'] = r_min # Min value of r. It must be between 0 and Max.
        # Camera system parameters
        owner['gamma_c_a'] = gamma_c_a # Return coefficient of Camera in range between 0 and 1. 0 : instant return, 1 : no return
        owner['gamma_c_r'] = gamma_c_r # Return coefficient of Camera in range between 0 and 1. 0 : instant return, 1 : no return
        owner['gamma_t'] = gamma_t # Return coefficient of Target in range between 0 and 1. 0 : no return, 1 : instant return
        # Camera system objects:
        owner['Center'] = scene.objects["Player"]
        owner['Target_eq'] = scene.objects["Player"]
        owner['Target'] = owner['Target_eq'].position
        # Camera game object
        if debugState:
            owner['Camera'] = scene.addObject("CameraDebug", owner, 0)
        else:
            owner['Camera'] = scene.addObject("DynCamera", owner, 0)
            owner['Camera'].useViewport = True
            owner['Camera'].setViewport(0,0,width, height)
            owner['Camera'].setOnTop()
            scene.active_camera.endObject() # End defaut camera
        owner['Camera'].position = owner['Center'].position + mathutils.Vector((0.0, 0.0, 1.0)) # Set starting camera position
        # Init is True
        owner['init'] = True

def update_camera(owner, delta_phi, delta_theta, delta_r):
    # Updte phi
    if delta_phi is not 0:
        phi_new = owner['phi'] - delta_phi
        if phi_new < 0:
            owner['phi'] = phi_new + 2*math.pi
        elif phi_new > 2*math.pi:
            owner['phi'] = phi_new - 2*math.pi
        else:
            owner['phi'] = phi_new
    # Update theta
    if delta_theta is not 0:
        theta_new = owner['theta'] + delta_theta
        if theta_new  > owner['theta_max']:
            owner['theta'] = owner['theta_max']
        elif theta_new  < owner['theta_min']:
            owner['theta'] = owner['theta_min']
        else:
            owner['theta'] = theta_new
    # Update r
    if delta_r is not 0:
        r_new = owner['r'] + delta_r
        if r_new  > owner['r_max']:
            owner['r'] = owner['r_max']
        elif r_new  < owner['r_min']:
            owner['r'] = owner['r_min']
        else:
            owner['r'] = r_new
    # Update Camera_eq
    cos_theta = math.cos(owner['theta'])
    Camera_eq = mathutils.Vector((cos_theta * math.sin(owner['phi']), cos_theta * math.cos(owner['phi']), math.sin(owner['theta'])))
    # Update Target_eq
    owner['Target'] = (owner['Target']).lerp(owner['Target_eq'].position, owner['gamma_t'])
    # Update camera position
    #   Orientation
    quat_rotation = Camera_eq.rotation_difference(owner['Camera'].position - owner['Center'].position) # Angle between Camera and Camera_eq w.r.t. Center
    quat_rotation.angle = owner['gamma_c_a'] * quat_rotation.angle
    Camera_versor = Camera_eq.normalized()
    (Camera_versor).rotate(quat_rotation)
    #   Distance
    length = owner['r'] + ((owner['Camera'].position - owner['Center'].position).length - owner['r'])*owner['gamma_c_r']
    Ray = owner['Center'].rayCast(owner['Center'].position + Camera_versor, None, max(length,2*owner['r_max']), 'Wall', 1, 1) # Ray from Center to Center+Camera_versor*Max(r_max,owner['r'])
    if Ray[0] is not None:
        r_Ray = 0.9*(Ray[1] - owner['Center'].position).length
        if r_Ray < length:
            length = r_Ray
    owner['Camera'].position = (Camera_eq.normalized())*length
    (owner['Camera'].position).rotate(quat_rotation)
    owner['Camera'].position = owner['Center'].position + (owner['Camera'].position)
    # Update cameta direction
    r = owner['Camera'].position - owner['Target']
    owner['Camera'].alignAxisToVect(mathutils.Vector((-r[0]*r[2], -r[1]*r[2], r[0]*r[0] + r[1]*r[1])), 1,1.0) # Aligne Camera to Tild direction
    owner['Camera'].alignAxisToVect(r, 2,1.0) # Aligne Camera to Target
    #DEBUG
    if debugState == True:
        Camera_eqZ = mathutils.Vector((0, 0, Camera_eq[2]))
        bge.render.drawLine(owner['Center'].position, owner['Center'].position + Camera_eqZ, Blue)
        Camera_eqXY = mathutils.Vector((Camera_eq[0], Camera_eq[1], 0))
        bge.render.drawLine(owner['Center'].position, owner['Center'].position + Camera_eqXY, Blue)
        bge.render.drawLine(owner['Center'].position, owner['Center'].position + Camera_eq, Green)
        bge.render.drawLine(owner['Target_eq'].position, owner['Target'], Magenta)
        bge.render.drawLine(owner['Center'].position + Camera_eq, owner['Camera'].position, Magenta)
        Direction = mathutils.Vector((-r[0]*r[2], -r[1]*r[2], r[0]*r[0] + r[1]*r[1]))
        bge.render.drawLine(owner['Camera'].position, owner['Camera'].position + 0.2 * Direction.normalized(), Yellow)
        bge.render.drawLine(owner['Target'], owner['Camera'].position, Red)


main()
