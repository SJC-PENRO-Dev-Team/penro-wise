# Grouped Links Feature - Requirements

## Feature Overview
Merge multiple link attachments that share the same group/project name into a single visual item in the file manager. Clicking the grouped item opens a modal displaying all links in that group.

## User Stories

### US-1: View Grouped Links as Single Item
**As a** file manager user  
**I want** multiple links with the same group name to appear as one item  
**So that** the file manager is less cluttered and better organized

**Acceptance Criteria:**
- 1.1: Links with identical `link_title` values are grouped together
- 1.2: Only one visual item appears in the file manager per group
- 1.3: The grouped item displays the group name (e.g., "Project Three")
- 1.4: The grouped item shows a visual indicator (icon/badge) showing it contains multiple links
- 1.5: The count of links in the group is visible (e.g., "3 links")

### US-2: Access Individual Links via Modal
**As a** file manager user  
**I want** to click a grouped link item to see all links in that group  
**So that** I can access any specific link I need

**Acceptance Criteria:**
- 2.1: Clicking a grouped link item opens a modal
- 2.2: Modal title displays the group name
- 2.3: Modal lists all links in the group with their URLs
- 2.4: Each link in the modal is clickable
- 2.5: Clicking a link opens it in a new tab
- 2.6: Modal has a close button (X) and can be dismissed with ESC key
- 2.7: Modal shows link metadata (upload date, uploaded by)

### US-3: Move Grouped Links
**As a** file manager admin  
**I want** to move a grouped link item to another folder  
**So that** all links in the group are moved together

**Acceptance Criteria:**
- 3.1: Grouped link items can be dragged and dropped
- 3.2: Dropping a grouped item moves ALL links in the group
- 3.3: Context menu "Move" option works for grouped items
- 3.4: Bulk move includes grouped items (moves all links in group)
- 3.5: Success message indicates how many links were moved
- 3.6: All links in the group maintain their group name after move

### US-4: Delete Grouped Links
**As a** file manager admin  
**I want** to delete a grouped link item  
**So that** all links in the group are removed together

**Acceptance Criteria:**
- 4.1: Context menu "Delete" option works for grouped items
- 4.2: Delete confirmation shows the group name and link count
- 4.3: Confirming deletion removes ALL links in the group
- 4.4: Bulk delete includes grouped items (deletes all links in group)
- 4.5: Success message indicates how many links were deleted

### US-5: Rename Grouped Links
**As a** file manager admin  
**I want** to rename a grouped link item  
**So that** all links in the group get the new name

**Acceptance Criteria:**
- 5.1: Context menu "Rename" option works for grouped items
- 5.2: Rename modal shows current group name
- 5.3: Entering a new name updates ALL links in the group
- 5.4: Success message confirms the rename
- 5.5: Grouped item immediately reflects the new name

### US-6: Add Links to Existing Group
**As a** file manager admin  
**I want** to add new links with an existing group name  
**So that** they automatically join the existing group

**Acceptance Criteria:**
- 6.1: Creating a new link with an existing group name adds it to that group
- 6.2: The grouped item count updates automatically
- 6.3: The new link appears in the modal when opened
- 6.4: No duplicate grouped items are created

### US-7: Ungroup Single Link
**As a** file manager admin  
**I want** single links (not in a group) to display normally  
**So that** the interface remains consistent

**Acceptance Criteria:**
- 7.1: Links with unique `link_title` values display as individual items
- 7.2: Single links do not show a group indicator or count
- 7.3: Clicking a single link opens the link directly (no modal)
- 7.4: Single links can be moved, deleted, renamed individually

### US-8: Bulk Operations on Mixed Selection
**As a** file manager admin  
**I want** to select both grouped and individual items  
**So that** I can perform bulk operations efficiently

**Acceptance Criteria:**
- 8.1: Checkboxes work for grouped link items
- 8.2: Selecting a grouped item selects all links in the group
- 8.3: Selection count reflects total number of links (not groups)
- 8.4: Bulk move/delete operations handle grouped items correctly
- 8.5: Mixed selections (files, folders, grouped links, single links) work together

## Data Model Considerations

### Current Structure
```python
class WorkItemAttachment:
    link_url = URLField()          # The actual URL
    link_title = CharField()       # Group/project name (used for grouping)
    folder = ForeignKey()          # Current folder location
    acceptance_status = CharField() # "accepted", "pending", "rejected"
```

### Grouping Logic
- **Group Key**: `link_title` + `folder` (links are grouped by title within the same folder)
- **Why folder matters**: Same group name in different folders = different groups
- **Empty titles**: Links without `link_title` are treated as individual items

## Technical Approach

### Backend Changes
1. **View Layer** (`file_manager_view`):
   - Group attachments by `link_title` where `link_url` is not null
   - Pass grouped data structure to template
   - Structure: `{ group_name: [link1, link2, ...], ... }`

2. **New Endpoint** (`get_grouped_links`):
   - Returns all links for a specific group name in a folder
   - Used by modal to fetch link details
   - JSON response with link data

3. **Bulk Operations**:
   - Update move/delete/rename to handle grouped items
   - When operating on a group, affect all links with that `link_title`

### Frontend Changes
1. **Template** (`file_manager.html`):
   - Render grouped items differently from individual items
   - Add group indicator icon and count badge
   - Update data attributes for grouped items

2. **Modal** (new):
   - Create "Grouped Links Modal" component
   - Fetch and display all links in group
   - Make links clickable (open in new tab)

3. **JavaScript**:
   - Update drag/drop to handle grouped items
   - Update selection logic to count all links in group
   - Update context menu for grouped items

## Edge Cases

### EC-1: Empty Group Name
- **Scenario**: Link has no `link_title` (null or empty)
- **Behavior**: Treat as individual item, display URL or "Untitled Link"

### EC-2: Single Link in Group
- **Scenario**: Only one link has a specific `link_title`
- **Behavior**: Display as individual item (no grouping needed)

### EC-3: Group Across Folders
- **Scenario**: Same `link_title` exists in multiple folders
- **Behavior**: Each folder has its own group (grouping is folder-specific)

### EC-4: Partial Delete
- **Scenario**: User deletes some links from a group manually
- **Behavior**: Group count updates; if only 1 link remains, becomes individual item

### EC-5: Rename Conflict
- **Scenario**: Renaming a group to match another existing group name
- **Behavior**: Merge the groups (all links now share the same name)

### EC-6: Move Partial Group
- **Scenario**: User moves some links from a group to another folder
- **Behavior**: Not possible via UI (grouped items move together); manual DB changes would split the group

## Non-Functional Requirements

### Performance
- NFR-1: Grouping logic must not significantly slow down folder view loading
- NFR-2: Modal should load link details within 500ms
- NFR-3: Bulk operations on grouped items should complete within 3 seconds for up to 100 links

### Usability
- NFR-4: Grouped items must be visually distinct from individual items
- NFR-5: Modal must be accessible (keyboard navigation, screen readers)
- NFR-6: Group count badge must be clearly visible

### Compatibility
- NFR-7: Feature must work on mobile devices (touch-friendly modal)
- NFR-8: Drag and drop must work for grouped items on all supported browsers
- NFR-9: Existing link functionality must not be broken

## Success Metrics
- SM-1: File manager displays fewer items when links are grouped (reduction in visual clutter)
- SM-2: Users can access all links in a group within 2 clicks
- SM-3: Bulk operations on grouped items work without errors
- SM-4: No performance degradation in folder view loading times

## Out of Scope (Future Enhancements)
- Custom grouping rules (beyond `link_title`)
- Nested groups or hierarchical link organization
- Link preview/thumbnails in modal
- Drag individual links out of a group
- Group-level permissions or access control
- Link validation or health checks
- Automatic grouping suggestions based on URL patterns

## Dependencies
- Existing link attachment system
- File manager UI and drag/drop functionality
- Modal component library (Bootstrap modals)
- Bulk operation infrastructure

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Grouping logic slows down queries | High | Use database aggregation, add indexes on `link_title` |
| Users confused by grouped items | Medium | Clear visual indicators, tooltips, help text |
| Bulk operations fail for large groups | Medium | Add batch processing, progress indicators |
| Modal doesn't load on slow connections | Low | Add loading spinner, timeout handling |
| Rename conflicts cause data loss | High | Implement confirmation dialog for merges |

## Assumptions
- A-1: Users understand that links with the same name are related
- A-2: Group names are meaningful and descriptive
- A-3: Most groups will have 2-10 links (not hundreds)
- A-4: Users want to manage grouped links as a unit
- A-5: Opening links in new tabs is the desired behavior

## Questions for Stakeholders
1. Should we allow ungrouping (splitting a group into individual links)?
2. What should happen if a group has 100+ links? Pagination in modal?
3. Should we show a preview of URLs in the grouped item (e.g., first 2 URLs)?
4. Do we need group-level metadata (description, tags, etc.)?
5. Should admins be able to manually group/ungroup links?
