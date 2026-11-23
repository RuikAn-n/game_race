using UnityEngine;

namespace Rupu
{
    public class Act1Patrol : MonoBehaviour
    {
        public float zMin = 40f;
        public float zMax = 48f;
        public float speed = 0.7f;

        private int direction = 1;

        private void Update()
        {
            if (Act1DirectorBlock.IsBlocked) return;

            Vector3 position = transform.position;
            position.z += speed * direction * Time.deltaTime;
            if (position.z >= zMax) direction = -1;
            if (position.z <= zMin) direction = 1;
            transform.position = position;
            transform.rotation = Quaternion.Euler(0f, direction > 0 ? 0f : 180f, 0f);
        }
    }

    public static class Act1DirectorBlock
    {
        public static bool IsBlocked
        {
            get
            {
                Act1Director director = Object.FindObjectOfType<Act1Director>();
                return director != null && director.BlocksMovement;
            }
        }
    }
}
