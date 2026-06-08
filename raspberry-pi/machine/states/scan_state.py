import cv2
import numpy as np

from utils.debug import get_logger
from machine.base_state import BaseState

logger = get_logger("states.scan")

SCAN_FORWARD_VY = 32
SCAN_LATERAL_VX = 32
SCAN_ROTATION_VANG = 16
SCAN_AND_THRESHOLD_PX = 10
SCAN_CONFIRM_FRAMES = 4


class ScanState(BaseState):
    def __init__(self, state_machine):
        self.sm = state_machine
        self.confirm_count = 0

    @property
    def id(self):
        return self.sm.current_job.marker_id

    def enter(self):
        logger.info("Entering scan state")
        return None

    def execute(self):
        frame = self.sm.robot.camera.get_frame()
        if frame is None:
            return None

        res = self.sm.robot.aruco_detector.detect(frame, expected_ids=[self.id])
        if res != []:
            self.confirm_count += 1
            self.sm.robot.motors.stop_motors()
            logger.debug(
                f"ArUco {self.id} detected ({self.confirm_count}/{SCAN_CONFIRM_FRAMES})"
            )
            if self.confirm_count >= SCAN_CONFIRM_FRAMES:
                from .moving_state import MovingState
                from websocket.utils.messages import ArucoFoundMessage

                self.sm.publish(ArucoFoundMessage(marker_id=self.id))
                return MovingState(self.sm, res[0])
            return None

        if self.confirm_count != 0:
            logger.debug(f"ArUco {self.id} lost, resetting confirm counter")
            self.confirm_count = 0

        segmentor = self.sm.robot.table_segmentor
        mask = segmentor.detect(frame)
        stats = segmentor.last_stats

        if stats.get("kept_scores"):
            scores = stats["kept_scores"]
            logger.info(
                f"SEG | det:{stats['n_after_nms']}/{stats['n_above_conf']}/{stats['n_candidates']} "
                f"conf:{min(scores):.2f}/{max(scores):.2f}/{sum(scores)/len(scores):.2f} "
                f"(min/max/avg) | table:{stats['table_pct']:.1f}% "
                f"| top5_raw:{[f'{s:.2f}' for s in stats['top5_raw_scores']]}"
            )
        else:
            logger.info(
                f"SEG | no detection | "
                f"top5_raw:{[f'{s:.2f}' for s in stats.get('top5_raw_scores', [])]}"
            )

        non_table = cv2.bitwise_not(mask)
        h, w = mask.shape[:2]
        bottom_half = np.zeros((h, w), dtype=np.uint8)
        bottom_half[h // 5 :, w // 4 : 3 * w // 4] = 255
        and_mask = cv2.bitwise_and(non_table, bottom_half)

        and_count = cv2.countNonZero(and_mask)
        if and_count > SCAN_AND_THRESHOLD_PX:
            left_count = cv2.countNonZero(and_mask[:, : w // 2])
            right_count = cv2.countNonZero(and_mask[:, w // 2 :])
            if right_count > left_count:
                action = "LEFT"
                logger.verbose("Non-table on right, translating left")
                self.sm.robot.motors.setDirectionAndSpeed(-SCAN_LATERAL_VX, 0, 0)
            else:
                action = "CCW"
                logger.verbose("Non-table in bottom half, rotating CCW")
                self.sm.robot.motors.setDirectionAndSpeed(0, 0, -SCAN_ROTATION_VANG)
        else:
            action = "FORWARD"
            logger.verbose("Table clear ahead, moving forward")
            self.sm.robot.motors.setDirectionAndSpeed(0, SCAN_FORWARD_VY, 0)

        self._draw_debug(frame, mask, and_mask, action, and_count)

        return None

    def _draw_debug(self, frame, mask, and_mask, action, and_count):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        overlay[mask > 0] = [0, 255, 0]
        overlay[and_mask > 0] = [0, 0, 255]
        result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
        cv2.rectangle(result, (w // 4, h // 5), (3 * w // 4 - 1, h - 1), (0, 255, 255), 1)
        cv2.line(result, (w // 2, h // 5), (w // 2, h - 1), (0, 255, 255), 1)
        cv2.imshow("frame", result)
        cv2.waitKey(1)

    def exit(self):
        logger.info("Exiting scan state")
        self.sm.robot.motors.stop_motors()
        return None
