# Keyframe Reducer v1.2 by Richard Frazer 
import nuke
import math
import nukescripts

class doFixGimbalFlipPanel(nukescripts.PythonPanel):
	def __init__(self, node):
	
		#get reference of tKey knob
		knob_names = nuke.animations()	
		knob_name_with_suffix = knob_names[0]
		#print"knob_name_with_suffix "
		#print knob_name_with_suffix
		knob_name = getKnobName(knob_name_with_suffix)
		k = nuke.thisNode()[knob_name]

		#so that our default frame range can be the length of it's keyframes
		tFirst = first_keyframe_location(k)
		tLast = last_keyframe_location(k)
		
		nukescripts.PythonPanel.__init__(self, 'Fix Gimbal Flip in selected animation?')
		
		# CREATE KNOBS
		self.tFrameRange = nuke.String_Knob('tFrameRange', 'Frame Range', '%s-%s' % (tFirst, tLast))
		self.tErrorPercent = nuke.Double_Knob('tErrorPercent', 'Threshold (degrees)')
		self.tErrorPercent.setValue(10)
		self.tErrorPercent.setRange(1,180)
		
		self.pcText = nuke.Text_Knob( 'degrees' )
		self.pcText.clearFlag( nuke.STARTLINE )
		
		# ADD KNOBS
		for k in (self.tFrameRange, self.tErrorPercent):
			self.addKnob(k)



def getKnobName(knob_name_with_suffix):
	
	# THIS NEEDS IMPROVING
	# if we try to run this script on transforms applied to Beziers or Layers within a RotoPaint node, they fall under the knob "curves"
	# i.e. "curves.Bezier1.rotate" or "curves.translate.x". Nuke gets a bit weird when trying to expression link to these attributes, the 
	# naming conventions start getting randomly inconsistent. It probably all falls under the _curvelib.AnimCTransform object type. 

	knob_name = knob_name_with_suffix.split(".")[0]
	#print "knob_name " + knob_name
	return knob_name

def getKnobIndex():

	#useful function by Ivan Busquets 

	tclGetAnimIndex = """

	set thisanimation [animations]
	if {[llength $thisanimation] > 1} {
		return "-1"
	} else {
		return [lsearch [in [join [lrange [split [in $thisanimation {animations}] .] 0 end-1] .] {animations}] $thisanimation]
	}
	"""

	return int(nuke.tcl(tclGetAnimIndex))


def first_keyframe_location(k):

	#Returns the first frame which contains an animated keyframe for the selected node

	first_frames = []
	# Walk all the knobs of the object and check if they are animated.
	if k.isAnimated():
		for tOriginalCurve in k.animations():
			tKeys = tOriginalCurve.keys()
			#print len(tKeys)
			if len(tKeys):
				first_frames.append(tKeys[0].x)
		print first_frames
		return int(min(first_frames))
	else:
		return nuke.root().firstFrame()
	
	
def last_keyframe_location(k):

	#Returns the last frame which contains an animated keyframe for the selected node

	last_frames = []
	# Walk all the knobs of the object and check if they are animated.
	if k.isAnimated():
		for tOriginalCurve in k.animations():
			tKeys = tOriginalCurve.keys()
			if len(tKeys):
				last_frames.append(tKeys[len(tKeys)-1].x)
		#print last_frames
		return int(max(last_frames))
	else:
		return nuke.root().lastFrame()
	



def doFixGimbalFlip():	

	p = doFixGimbalFlipPanel(nuke.selectedNode())
		
	if p.showModalDialog(): #user did not hit cancel button

		undo = nuke.Undo()
		undo.begin("Fix Gimbal Flip")  

		tErrorPercent = p.tErrorPercent.value()
		
		if (tErrorPercent > 100):
			tErrorPercent = 100
		
		if (tErrorPercent < 0.000001):
			tErrorPercent = 0.000001

		tFrameRange =  nuke.FrameRange( p.tFrameRange.value() )
		tFirstFrame = tFrameRange.first()
		tLastFrame = tFrameRange.last()
		
		knob_names = nuke.animations() # Returns the animations names under this knob
		
		i=getKnobIndex() #find out if user only clicked on a single knob index, or the entire knob
		
		print "knob index: " + str(i)

		j=0 #index for knob

		#print " knob_names " + str( knob_names)
		 
		for knob_name_with_suffix in knob_names: 

			#print "knob_name_with_suffix " + str(knob_name_with_suffix)

			if(i > -1):
				j = i
			
			#print "for knob_name_with_suffix in knob_names:"
			
			knob_name = getKnobName(knob_name_with_suffix)
			
			# so that we can get at the knob object and do...
			k = nuke.thisNode()[knob_name]

			print knob_name + "." + str(j)

			if(k.isAnimated(j)):
			
				tOriginalCurve = k.animation(j)
				
				tKeys = tOriginalCurve.keys()

				#tOrigFirstFrame = tKeys[0].x
				
				#tOrigLastFrame = tKeys[len(tKeys)-1].x
												
				tKeysLen = len(tKeys)
				
				tLastValue = tKeys[0].y

				#print "tErrorThreshold " + str(tErrorThreshold)
				


				n = nuke.selectedNode()
				
				for f in range(0, tKeysLen):

					tFrame = tKeys[f].x

					if ( tFrame >= tFirstFrame ) and ( tFrame <= tLastFrame ):

						tValue = tKeys[f].y
						#print "tValue " + str(tValue)
						tLastDiff = tLastValue - tValue
						tPredictedValue = tValue + tLastDiff
						tDiff = tPredictedValue - tValue

						#print str(tFrame) + " tLastValue " + str(tLastValue) + " tValue " + str(tValue) + " tLastDiff " + str(tLastDiff)

						#print str(tFrame) + " tPredictedValue " + str(tPredictedValue) + " tValue " + str(tValue) + " tDiff " + str(tDiff)
						if(tDiff > (180-tErrorPercent))|(tDiff < -(180-tErrorPercent)):
							print "gimbal flip at " + str(tFrame)
							print str(tFrame) + " tPredictedValue " + str(tPredictedValue) + " tValue " + str(tValue) + " tDiff " + str(tDiff)
							#print "fixing keys " + str(i) + " to " + str(tKeysLen)
							print "fixing frames " + str(tKeys[f].x) + " to " + str(tKeys[tKeysLen-1].x)
							for k in range(f, tKeysLen):
								#k.animation(j)
								tFixFrame = tKeys[k].x

								if ( tFixFrame >= tFirstFrame ) and ( tFixFrame <= tLastFrame ):

									tOldValue = tKeys[k].y

									if ( tDiff > 0 ):
										tNewValue = tOldValue + 180
									else:
										tNewValue =  tOldValue - 180

									#print str(tFixFrame) + " tOldValue " + str(tOldValue) + " tNewValue " + str(tNewValue)

									tOriginalCurve.setKey(tFixFrame, tNewValue)

							if ( tDiff > 0 ):
								tLastValue = tValue + 180
							else:
								tLastValue = tValue - 180
							

						else:
							tLastValue = tValue

			else:
			
				print "No animation found in " + knob_name + " index " + str(j)
				
			#break the loop if we are only running script on single knob index
			if(i > -1):
				#print "breaking"
				break
			else:
				j=j+1
			#print "j " + str(j)


		undo.end()
	
	


