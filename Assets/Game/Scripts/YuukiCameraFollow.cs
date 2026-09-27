using UnityEngine;

public sealed class YuukiCameraFollow : MonoBehaviour
{
    [SerializeField] private Transform target;
    [SerializeField] private float horizontalOffset = 2f;
    [SerializeField] private float smoothing = 5f;

    public void SetTarget(Transform value)
    {
        target = value;
    }

    private void LateUpdate()
    {
        if (target == null)
            return;

        Vector3 desired = new Vector3(target.position.x + horizontalOffset, 0f, -10f);
        transform.position = Vector3.Lerp(transform.position, desired, Time.deltaTime * smoothing);
    }
}
