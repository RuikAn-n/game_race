using UnityEngine;

namespace Rupu
{
    public class Act1Player : MonoBehaviour
    {
        public Act1Director director;
        public float moveSpeed = 4.2f;
        public float lookSpeed = 2.2f;
        public float gravity = -22f;
        public float startYaw = 180f;

        private CharacterController controller;
        private Camera playerCamera;
        private Animator animator;
        private float yaw;
        private float pitch = 8f;
        private float verticalVelocity;
        private Vector3 focusTarget;
        private float focusUntil;

        public void LookAt(Vector3 target, float duration)
        {
            focusTarget = target;
            focusUntil = Time.time + duration;
            Debug.Log($"[Act1] 镜头转向 {target.x:0},{target.z:0}");
        }

        private void Start()
        {
            controller = GetComponent<CharacterController>();
            animator = GetComponentInChildren<Animator>();
            yaw = startYaw;
            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            playerCamera = Camera.main;
            if (playerCamera != null)
            {
                playerCamera.transform.SetParent(transform, false);
                playerCamera.transform.localPosition = new Vector3(0f, 1.75f, -3.4f);
                playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
                playerCamera.farClipPlane = 150f;
            }

            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        private void Update()
        {
            bool blocked = director != null && director.BlocksMovement;

            if (Time.time < focusUntil)
            {
                Vector3 direction = focusTarget - (transform.position + Vector3.up * 1.6f);
                float targetYaw = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg;
                float targetPitch = -Mathf.Atan2(direction.y, new Vector2(direction.x, direction.z).magnitude) * Mathf.Rad2Deg;
                yaw = Mathf.LerpAngle(yaw, targetYaw, Time.deltaTime * 4f);
                pitch = Mathf.Lerp(pitch, Mathf.Clamp(targetPitch, -30f, 55f), Time.deltaTime * 4f);
            }
            else
            {
                float mouseX = blocked ? 0f : Input.GetAxis("Mouse X") * lookSpeed;
                float mouseY = blocked ? 0f : Input.GetAxis("Mouse Y") * lookSpeed;
                yaw += mouseX;
                pitch = Mathf.Clamp(pitch - mouseY, -22f, 42f);
            }

            transform.rotation = Quaternion.Euler(0f, yaw, 0f);

            if (playerCamera != null) playerCamera.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
            UpdateCameraCollision();

            if (controller == null || !controller.enabled) return;

            Vector3 move = Vector3.zero;
            if (!blocked)
            {
                float h = Input.GetAxisRaw("Horizontal");                float v = Input.GetAxisRaw("Vertical");
                move = (transform.right * h + transform.forward * v).normalized * moveSpeed;
            }

            if (controller.isGrounded && verticalVelocity < 0f) verticalVelocity = -2f;
            verticalVelocity += gravity * Time.deltaTime;
            move.y = verticalVelocity;
            if (animator != null) animator.SetFloat("Speed", new Vector2(move.x, move.z).magnitude / Mathf.Max(0.01f, moveSpeed));
            controller.Move(move * Time.deltaTime);
        }

        private void UpdateCameraCollision()
        {
            if (playerCamera == null) return;
            const float desiredDistance = 3.4f;
            Vector3 origin = transform.position + Vector3.up * 1.7f;
            Vector3 direction = -transform.forward;
            RaycastHit hit;
            if (Physics.SphereCast(origin, 0.25f, direction, out hit, desiredDistance, ~0, QueryTriggerInteraction.Ignore))
            {
                float distance = Mathf.Clamp(hit.distance - 0.2f, 0.7f, desiredDistance);
                playerCamera.transform.localPosition = new Vector3(0f, 1.75f, -distance);
            }
            else
            {
                playerCamera.transform.localPosition = new Vector3(0f, 1.75f, -desiredDistance);
            }
        }

        public void Teleport(Vector3 position, float newYaw)
        {
            if (controller != null) controller.enabled = false;
            transform.position = position;
            yaw = newYaw;
            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            Physics.SyncTransforms();
            if (controller != null) controller.enabled = true;
        }
    }
}

